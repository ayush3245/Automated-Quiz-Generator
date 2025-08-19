from __future__ import annotations

from typing import Dict


def score_candidate(heur_ok: bool, judge: Dict, option_sim_mean: float) -> float:
	"""Compute a simple score for a candidate item."""
	s = 0.0
	s += 1.0 if heur_ok else 0.0
	s += 1.0 if judge.get("is_unambiguous") else 0.0
	s += 1.0 if judge.get("is_supported") else 0.0
	s += 0.5 if judge.get("grammar_ok") else 0.0
	s -= 0.5 if option_sim_mean >= 0.8 else 0.0
	return s


