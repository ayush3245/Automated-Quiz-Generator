from __future__ import annotations

from typing import Any, Dict

from .opik_shim import track
import json

from .llm import json_completion
from .prompts import DISTRACTOR_IMPROVER, QUESTION_PROMPT
from .schemas import ItemSchema


@track()
def generate_item(chunk: str, *, model: str, temperature: float = 0.0) -> Dict[str, Any]:
	"""Generate a single MCQ item from a chunk of text.

	1) Ask for a question
	2) Improve distractors
	"""
	first = json_completion(
		QUESTION_PROMPT.format(passage=chunk), model=model, temperature=temperature, schema=ItemSchema
	)
	second = json_completion(
		DISTRACTOR_IMPROVER.format(item_json=json.dumps(first, ensure_ascii=False)),
		model=model,
		temperature=temperature,
		schema=ItemSchema,
	)
	return second


