from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess


def test_cli_generates_jsonl(tmp_path: Path):
	# Skip if no API key present
	if not os.getenv("GROQ_API_KEY"):
		import pytest

		pytest.skip("GROQ_API_KEY not set; skipping integration smoke test")

	proj_root = Path(__file__).resolve().parents[1]
	input_path = proj_root / "quizgen" / "data" / "sample.txt"
	out_path = tmp_path / "test.jsonl"
	cmd = [
		"python",
		"-m",
		"quizgen.app",
		"--input",
		str(input_path),
		"--n",
		"2",
		"--out",
		str(out_path),
		"--model",
		"llama-3.1-8b-instant",
		"--temperature",
		"0.2",
	]
	res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(proj_root))
	assert res.returncode == 0, res.stderr
	assert out_path.exists()

	lines = out_path.read_text(encoding="utf-8").strip().splitlines()
	assert len(lines) >= 2
	for line in lines:
		obj = json.loads(line)
		for key in ["source_id", "question", "options", "answer_index", "explanation"]:
			assert key in obj
		assert isinstance(obj["options"], list) and len(obj["options"]) == 4


