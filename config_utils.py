#!/usr/bin/env python3
"""Utility helpers for reading environment-driven configuration values."""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

_DEFAULT_REQUEST_TIMEOUT = 10.0
_FALLBACK_OPERATION_TIMEOUT = 1.0
_BUFFER_SECONDS = 1.5


def _parse_positive_float(raw_value: str | None, default: float, env_name: str) -> float:
    """Return a positive float from an environment variable or the provided default."""
    if raw_value is None:
        return default

    try:
        parsed = float(raw_value)
    except (TypeError, ValueError):
        logger.warning("Invalid %s value %r; using default %.1f seconds", env_name, raw_value, default)
        return default

    if parsed <= 0:
        logger.warning("%s must be greater than zero; using default %.1f seconds", env_name, default)
        return default

    return parsed


def get_request_timeout() -> float:
    """Return the HTTP request timeout (in seconds) for Stepstone calls."""
    return _parse_positive_float(os.environ.get("REQUEST_TIMEOUT"), _DEFAULT_REQUEST_TIMEOUT, "REQUEST_TIMEOUT")


def get_operation_timeout() -> float:
    """Return the maximum time (in seconds) to wait for long-running operations."""
    request_timeout = get_request_timeout()
    candidate = request_timeout - _BUFFER_SECONDS
    if candidate < _FALLBACK_OPERATION_TIMEOUT:
        candidate = min(request_timeout, _FALLBACK_OPERATION_TIMEOUT)
    return max(candidate, 1.0)
