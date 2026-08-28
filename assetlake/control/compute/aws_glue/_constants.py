"""Shared constants for AWS Glue compute."""

from __future__ import annotations

_TERMINAL_STATES: frozenset[str] = frozenset({"SUCCEEDED", "FAILED", "ERROR", "TIMEOUT", "STOPPED"})
