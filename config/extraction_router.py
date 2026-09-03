"""Choose Ollama vs paid LLM for Graphiti extraction based on burst size.

Small writes stay on local Ollama (free). A burst of THRESHOLD or more
episodes in WINDOW_SEC seconds uses the paid API already configured in .env
so a CPU-only host is not crushed. Embeddings stay on Ollama either way.

The route is decided at process time, not enqueue time, so N parallel
add_memory calls that arrive together all see each other.
"""

from __future__ import annotations

import os
import threading
import time

THRESHOLD = int(os.getenv('EXTRACTION_PAID_THRESHOLD', '5'))
WINDOW_SEC = float(os.getenv('EXTRACTION_BURST_WINDOW_SEC', '8'))

_lock = threading.Lock()
_enqueued_at: list[float] = []


def mark_enqueued() -> float:
    """Record an enqueue timestamp. Returns monotonic time for later routing."""
    now = time.monotonic()
    cutoff = now - max(WINDOW_SEC * 4, 60.0)
    with _lock:
        _enqueued_at.append(now)
        _enqueued_at[:] = [t for t in _enqueued_at if t > cutoff]
    return now


def choose(enqueued_at: float) -> str:
    """Return 'ollama' if this episode's burst is below threshold, else 'paid'.

    Fewer than THRESHOLD episodes in the same WINDOW_SEC window -> Ollama.
    THRESHOLD or more (including exactly 5) -> paid API from LLM_PROVIDER.
    """
    with _lock:
        n = sum(1 for t in _enqueued_at if abs(t - enqueued_at) <= WINDOW_SEC)
    if n < THRESHOLD:
        return 'ollama'
    return 'paid'


def describe() -> str:
    ollama_model = os.getenv('OLLAMA_MODEL_NAME', 'qwen2.5-brain')
    return (
        f'burst<{THRESHOLD} in {WINDOW_SEC:.0f}s -> ollama ({ollama_model}); '
        f'{THRESHOLD}+ -> paid LLM_PROVIDER'
    )
