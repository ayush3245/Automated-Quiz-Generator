from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Dict, Optional, Type

from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError
from .opik_shim import track, opik_context
from groq import Groq


def _strip_code_fences(text: str) -> str:
	"""Remove markdown code fences and surrounding whitespace."""
	if text is None:
		return ""
	text = text.strip()
	# Remove ```json ... ``` or ``` ... ``` fences
	text = re.sub(r"^```[a-zA-Z]*\n", "", text)
	text = re.sub(r"\n```$", "", text)
	return text.strip()


def _extract_json_block(text: str) -> str:
	"""Best-effort extraction of a JSON object from text."""
	text = _strip_code_fences(text)
	# Attempt direct parse first
	try:
		json.loads(text)
		return text
	except Exception:
		pass
	# Extract first {...} block with balanced braces heuristic
	start = text.find("{")
	end = text.rfind("}")
	if start != -1 and end != -1 and end > start:
		candidate = text[start : end + 1]
		return candidate
	return text


def get_client() -> Groq:
	"""Return a Groq client for chat completions."""
	load_dotenv()
	api_key = os.getenv("GROQ_API_KEY")
	if not api_key:
		raise RuntimeError("GROQ_API_KEY not set. Create .env or export env var.")
	client = Groq(api_key=api_key)
	return client


@track()
def json_completion(
	prompt: str,
	*,
	model: str,
	temperature: float = 0.0,
	max_retries: int = 3,
	timeout_sec: float = 60.0,
	schema: Optional[Type[BaseModel]] = None,
) -> Dict[str, Any]:
	"""Call the LLM and return a parsed JSON dict.

	Retries with exponential backoff and attempts to robustly parse JSON.
	"""
	client = get_client()
	opik_context.update_current_trace(metadata={
		"model": model,
		"temperature": temperature,
	})

	last_error: Optional[Exception] = None
	for attempt in range(1, max_retries + 1):
		try:
			resp = client.chat.completions.create(
				model=model,
				messages=[
					{"role": "user", "content": prompt},
				],
				temperature=temperature,
			)
			text = resp.choices[0].message.content or ""
			json_text = _extract_json_block(text)
			data = json.loads(json_text)
			if schema is not None:
				try:
					model_obj = schema.model_validate(data)
					data = model_obj.model_dump()
				except ValidationError as ve:  # noqa: PERF203
					raise ve
			if not isinstance(data, dict):
				raise ValueError("Model did not return a JSON object.")
			return data
		except Exception as e:  # noqa: BLE001
			last_error = e
			if attempt < max_retries:
				time.sleep(0.6 * attempt)
				continue
			raise


