from __future__ import annotations

from typing import Iterable, List


def _split_paragraphs(text: str) -> List[str]:
	paras = [p.strip() for p in text.split("\n\n")]
	return [p for p in paras if p]


def _split_sentences(paragraph: str) -> List[str]:
	# Very simple sentence splitter by punctuation. Avoids external deps.
	import re

	sentences = re.split(r"(?<=[.!?])\s+", paragraph.strip())
	return [s.strip() for s in sentences if s.strip()]


def _yield_chunks_from_sentences(sentences: Iterable[str], *, target_chars: int = 3000) -> Iterable[str]:
	current: List[str] = []
	length = 0
	for s in sentences:
		if length + len(s) + 1 > target_chars and current:
			yield " ".join(current).strip()
			current = [s]
			length = len(s) + 1
		else:
			current.append(s)
			length += len(s) + 1
	if current:
		yield " ".join(current).strip()


def chunk_text(text: str, *, target_chars: int = 3000) -> List[str]:
	"""Split text into chunks roughly matching target length while respecting paragraphs.

	We approximate 450 tokens as about 3000-3500 characters; default 3000.
	"""
	chunks: List[str] = []
	for para in _split_paragraphs(text):
		sentences = _split_sentences(para)
		for ch in _yield_chunks_from_sentences(sentences, target_chars=target_chars):
			if ch:
				chunks.append(ch)
	return chunks


