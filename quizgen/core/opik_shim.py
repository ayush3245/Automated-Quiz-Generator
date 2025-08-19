from __future__ import annotations

from typing import Any, Callable, Optional, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def _noop_track(func: Optional[F] = None, *args: Any, **kwargs: Any):  # type: ignore[misc]
	def decorator(f: F) -> F:  # type: ignore[override]
		return f

	if func is None:
		return decorator
	return decorator(func)


class _NoOpContext:
	def update_current_trace(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
		return None


def _identity_wrapper(x: Any) -> Any:
	return x


try:
	from opik import track as _real_track, opik_context as _real_context  # type: ignore
	from opik.integrations.openai import track_openai as _real_track_openai  # type: ignore

	track = _real_track  # noqa: N816
	opik_context = _real_context  # noqa: N816

	def get_track_openai() -> Callable[[Any], Any]:
		return _real_track_openai

except Exception:  # noqa: BLE001
	# Graceful fallback when Opik cannot import (e.g., bad config file)
	track = _noop_track  # type: ignore[assignment]
	opik_context = _NoOpContext()  # type: ignore[assignment]

	def get_track_openai() -> Callable[[Any], Any]:
		return _identity_wrapper


