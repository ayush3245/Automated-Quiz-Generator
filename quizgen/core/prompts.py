"""Prompt templates for the quiz generator."""

QUESTION_PROMPT = """
SYSTEM: You are a careful exam writer. Create ONE multiple-choice question from the passage.

RULES:
- Exactly 4 options, only one is correct.
- Plausible distractors; avoid overlaps; no giveaways.
- Require understanding of the passage; avoid verbatim copying.
- Return valid JSON ONLY (no commentary).

PASSAGE:
{passage}

OUTPUT JSON SCHEMA:
{{"question": "...", "options": ["...","...","...","..."], "answer_index": 0-3, "explanation": "..."}}
""".strip()

DISTRACTOR_IMPROVER = """
Improve the distractors to be plausible-but-wrong and non-overlapping with the correct answer.
Keep exactly 4 options and the same JSON schema. Return JSON only.

CURRENT ITEM:
{item_json}
""".strip()

JUDGE_PROMPT = """
Given the PASSAGE and MCQ, check:
- single unambiguous correct option (true/false),
- answer supported by the passage (true/false),
- grammar ok (true/false),
- difficulty 1..5 with a short rationale.

Return JSON only:
{{"is_unambiguous": true, "is_supported": true, "grammar_ok": true, "difficulty": 3, "notes": "..."}}
PASSAGE:
{passage}

MCQ:
{item_json}
""".strip()


