from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import typer
from dotenv import load_dotenv
from .core.opik_shim import track, opik_context
from tqdm import tqdm

from .core.chunk import chunk_text
from .core.generate import generate_item
from .core.score import score_candidate
from .core.validate import HeuristicResult, heuristic_check, judge_item


app = typer.Typer(add_completion=False, help="quizgen – Automated Quiz Generator with Opik observability")


@dataclass
class ItemRecord:
	item: Dict
	judge: Dict
	heur: HeuristicResult
	score: float
	chunk_id: str
	option_similarity_mean: float
	elapsed_sec: float


def _write_jsonl(path: Path, items: List[Dict]) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	with path.open("w", encoding="utf-8") as f:
		for it in items:
			json.dump(it, f, ensure_ascii=False)
			f.write("\n")


def _entropy_from_distribution(counts: List[int]) -> float:
	import math
	total = sum(counts) or 1
	p = [c / total for c in counts]
	return -sum((pi * math.log(pi, 2)) for pi in p if pi > 0)


@track()
def _build_quiz(
	*,
	text: str,
	n: int,
	model: str,
	temperature: float,
	max_candidates_per_chunk: int,
	feedback: Optional[float] = None,
) -> List[Dict]:
	chunks = chunk_text(text)
	selected: List[Dict] = []
	all_candidates: List[ItemRecord] = []
	opik_context.update_current_trace(metadata={
		"num_chunks": len(chunks),
		"target_items": n,
		"model": model,
		"temperature": temperature,
	})

	position_counts = [0, 0, 0, 0]
	start_time = time.time()

	for idx, chunk in enumerate(chunks, start=1):
		chunk_id = f"doc-001#chunk-{idx}"
		for _ in tqdm(range(max_candidates_per_chunk), desc=f"Chunk {idx}/{len(chunks)}", leave=False):
			t0 = time.time()
			item = generate_item(chunk, model=model, temperature=temperature)
			# basic fields enforcement
			item.setdefault("options", [])
			item.setdefault("question", "")
			item.setdefault("explanation", "")
			item.setdefault("answer_index", 0)

			heur = heuristic_check(item)
			judge, updated_item = judge_item(chunk, item, model=model, temperature=temperature)
			elapsed = time.time() - t0

			rec = ItemRecord(
				item=updated_item,
				judge=judge,
				heur=heur,
				score=score_candidate(heur.all_ok, judge, heur.option_similarity_mean),
				chunk_id=chunk_id,
				option_similarity_mean=heur.option_similarity_mean,
				elapsed_sec=elapsed,
			)
			all_candidates.append(rec)

	# Rank
	all_candidates.sort(key=lambda r: r.score, reverse=True)
	# Select with position rotation preference
	remaining = list(all_candidates)
	while len(selected) < n and remaining:
		# find least-used answer position
		target_pos = min(range(4), key=lambda i: position_counts[i])
		chosen_idx = None
		for idx_r, rec in enumerate(remaining):
			ai = int(rec.item.get("answer_index", 0))
			if ai == target_pos:
				chosen_idx = idx_r
				break
		# fallback to best available
		if chosen_idx is None:
			chosen_idx = 0
		rec = remaining.pop(chosen_idx)
		item = rec.item
		item["source_id"] = rec.chunk_id
		# attach time_sec into meta
		meta = item.get("meta") or {}
		meta["time_sec"] = int(round(rec.elapsed_sec))
		item["meta"] = meta
		selected.append(item)
		ai = int(item.get("answer_index", 0))
		if 0 <= ai < 4:
			position_counts[ai] += 1

	# Metrics
	total_time = time.time() - start_time
	valid_rate = sum(1 for r in all_candidates if r.heur.all_ok) / (len(all_candidates) or 1)
	avg_difficulty = sum(int(r.item.get("meta", {}).get("difficulty", 3)) for r in all_candidates) / (len(all_candidates) or 1)
	option_similarity_mean = sum(r.option_similarity_mean for r in all_candidates) / (len(all_candidates) or 1)
	position_bias_entropy = _entropy_from_distribution(position_counts)
	time_per_item = total_time / (len(selected) or 1)

	opik_context.update_current_trace(
		metadata={
			"metrics": {
				"valid_rate": valid_rate,
				"avg_difficulty": avg_difficulty,
				"option_similarity_mean": option_similarity_mean,
				"position_bias_entropy": position_bias_entropy,
				"time_per_item": time_per_item,
			},
		}
	)

	if feedback is not None:
		opik_context.update_current_trace(feedback_scores=[{"name": "user_feedback", "value": float(feedback)}])

	return selected


@app.command()
def main(
	input: Path = typer.Option(..., exists=True, dir_okay=False, help="Path to input .txt"),
	n: int = typer.Option(8, min=1, help="Number of items to generate"),
	out: Path = typer.Option(Path(f"runs/quiz_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"), help="Output JSONL path"),
	model: str = typer.Option("llama-3.1-8b-instant", help="Groq model"),
	temperature: float = typer.Option(0.2, help="Sampling temperature"),
	max_candidates_per_chunk: int = typer.Option(3, min=1, help="Candidates to generate per chunk"),
	feedback: Optional[float] = typer.Option(None, help="Optional feedback score to log to Opik"),
) -> None:
	"""Run the quiz generation pipeline and write a JSONL file."""
	load_dotenv()
	with input.open("r", encoding="utf-8") as f:
		text = f.read()

	items = _build_quiz(
		text=text,
		n=n,
		model=model,
		temperature=temperature,
		max_candidates_per_chunk=max_candidates_per_chunk,
		feedback=feedback,
	)
	_write_jsonl(out, items)
	typer.echo(f"Wrote {len(items)} items to {out}")


if __name__ == "__main__":
	app()


