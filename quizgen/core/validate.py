from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from .opik_shim import track
from rapidfuzz.distance import Levenshtein

from .llm import json_completion
from .prompts import JUDGE_PROMPT
from .schemas import JudgeSchema


@dataclass
class HeuristicResult:
	height_ok: bool
	answer_ok: bool
	length_ok: bool
	unique_ok: bool
	option_similarity_mean: float

	@property
	def all_ok(self) -> bool:
		return self.height_ok and self.answer_ok and self.length_ok and self.unique_ok


def _options_similarity_mean(options: List[str]) -> float:
	if len(options) < 2:
		return 0.0
	scores: List[float] = []
	for i in range(len(options)):
		for j in range(i + 1, len(options)):
			# Use normalized distance converted to similarity
			dist = Levenshtein.normalized_distance(options[i].lower(), options[j].lower())
			sim = 1.0 - dist  # 0..1, higher means more similar
			scores.append(sim)
	return sum(scores) / len(scores)


def heuristic_check(item: Dict) -> HeuristicResult:
	options = item.get("options") or []
	question = (item.get("question") or "").strip()
	explanation = (item.get("explanation") or "").strip()
	answer_index = item.get("answer_index")

	height_ok = len(options) == 4
	answer_ok = isinstance(answer_index, int) and 0 <= answer_index < 4
	length_ok = (
		50 <= len(question) <= 300 and 10 <= len(explanation) <= 600
	)

	# uniqueness via similarity threshold (fail if any pair >= 0.85)
	str_options = [str(o) for o in options]
	option_similarity_mean = _options_similarity_mean(str_options)
	unique_ok = True
	for i in range(len(str_options)):
		for j in range(i + 1, len(str_options)):
			if (1.0 - Levenshtein.normalized_distance(str_options[i].lower(), str_options[j].lower())) >= 0.85:
				unique_ok = False
				break
		if not unique_ok:
			break

	return HeuristicResult(
		height_ok=height_ok,
		answer_ok=answer_ok,
		length_ok=length_ok,
		unique_ok=unique_ok,
		option_similarity_mean=option_similarity_mean,
	)


@track()
def judge_item(passage: str, item: Dict, *, model: str, temperature: float = 0.0) -> Tuple[Dict, Dict]:
	"""LLM judge for an item. Returns (judge_dict, updated_item)."""
	prompt = JUDGE_PROMPT.format(passage=passage, item_json=item)
	judge = json_completion(prompt, model=model, temperature=temperature, schema=JudgeSchema)
	# Attach meta fields
	meta = item.get("meta") or {}
	meta.update({
		"difficulty": int(judge.get("difficulty")) if isinstance(judge.get("difficulty"), int) else 3,
		"judge_notes": str(judge.get("notes") or ""),
	})
	item["meta"] = meta
	return judge, item


