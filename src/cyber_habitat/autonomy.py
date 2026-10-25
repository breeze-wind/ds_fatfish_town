"""In-process, opt-in scheduling for one resident at a time."""

from __future__ import annotations

import threading
import time
from datetime import datetime
from typing import Callable


class AutonomousLife:
    def __init__(self, step: Callable[[str], None]):
        self._step = step
        self._wake = threading.Event()
        self._lock = threading.Lock()
        self._stopped = False
        self._enabled = False
        self._resident_id: str | None = None
        self._interval_seconds = 1800
        self._max_calls_per_day = 24
        self._day = datetime.now().date()
        self._calls_today = 0
        self._next_at: float | None = None
        self._in_flight = False
        self._last_error: str | None = None
        self._thread = threading.Thread(target=self._run, name="habitat-autonomy", daemon=True)
        self._thread.start()

    def configure(self, resident_id: str | None, *, enabled: bool,
                  interval_seconds: int = 1800, max_calls_per_day: int = 24) -> dict[str, object]:
        if enabled and not resident_id:
            raise ValueError("resident_id is required")
        if not 60 <= interval_seconds <= 86400:
            raise ValueError("interval_seconds must be from 60 to 86400")
        if not 1 <= max_calls_per_day <= 48:
            raise ValueError("max_calls_per_day must be from 1 to 48")
        with self._lock:
            self._roll_day()
            self._enabled = enabled
            self._resident_id = resident_id if enabled else None
            self._interval_seconds = interval_seconds
            self._max_calls_per_day = max_calls_per_day
            self._next_at = time.time() + interval_seconds if enabled else None
            self._last_error = None
            status = self._status_unlocked()
        self._wake.set()
        return status

    def status(self) -> dict[str, object]:
        with self._lock:
            self._roll_day()
            return self._status_unlocked()

    def _status_unlocked(self) -> dict[str, object]:
        return {"enabled": self._enabled, "resident_id": self._resident_id,
                "interval_seconds": self._interval_seconds,
                "max_calls_per_day": self._max_calls_per_day,
                "calls_today": self._calls_today, "in_flight": self._in_flight,
                "next_at": self._next_at, "last_error": self._last_error}

    def _roll_day(self) -> None:
        today = datetime.now().date()
        if today != self._day:
            self._day = today
            self._calls_today = 0

    def _run(self) -> None:
        while True:
            with self._lock:
                if self._stopped:
                    return
                self._roll_day()
                ready = (self._enabled and self._resident_id and
                         self._calls_today < self._max_calls_per_day and self._next_at is not None)
                delay = max(0.0, self._next_at - time.time()) if ready else 60.0
                resident_id = self._resident_id if ready and delay == 0 else None
                if resident_id:
                    self._calls_today += 1  # failed requests count against the cap
                    self._next_at = time.time() + self._interval_seconds
                    self._in_flight = True
            if resident_id:
                try:
                    self._step(resident_id)
                    error = None
                except Exception as exc:
                    error = type(exc).__name__
                with self._lock:
                    self._in_flight = False
                    self._last_error = error
                continue
            self._wake.wait(delay)
            self._wake.clear()

    def close(self) -> None:
        with self._lock:
            self._stopped = True
            self._enabled = False
        self._wake.set()
        self._thread.join(timeout=2)
