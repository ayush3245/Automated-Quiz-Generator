from __future__ import annotations

from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


class ItemSchema(BaseModel):
	question: str
	options: List[str] = Field(default_factory=list)
	answer_index: int
	explanation: str
	meta: Optional[Dict[str, Any]] = None


class JudgeSchema(BaseModel):
	is_unambiguous: bool
	is_supported: bool
	grammar_ok: bool
	difficulty: int = 3
	notes: Optional[str] = ""


