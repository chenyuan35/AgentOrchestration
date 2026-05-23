"""Configuration management module."""

import os
import json
import re
from typing import Any, Dict, Optional


# Sensitive key patterns for redaction
_SENSITIVE_PATTERNS = [
    re.compile(r'password', re.IGNORECASE),
    re.compile(r'secret', re.IGNORECASE),
    re.compile(r'token', re.IGNORECASE),
    re.compile(r'key', re.IGNORECASE),
    re.compile(r'credential', re.IGNORECASE),
    re.compile(r'auth', re.IGNORECASE),
    re.compile(r'private', re.IGNORECASE),
    re.compile(r'api_key', re.IGNORECASE),
    re.compile(r'apikey', re.IGNORECASE),
    re.compile(r'access_token', re.IGNORECASE),
    re.compile(r'refresh_token', re.IGNORECASE),
]

_REDACTED_PLACEHOLDER = "***REDACTED***"


def _is_sensitive_key(key: str) -> bool:
    """Check if a config key looks sensitive and should be redacted."""
    for pattern in _SENSITIVE_PATTERNS:
        if pattern.search(key):
            return True
    return False


def _redact_value(key: str, value: Any) -> Any:
    """Redact a single value if the key looks sensitive."""
    if _is_sensitive_key(key):
        return _REDACTED_PLACEHOLDER
    return value


def _redact_dict(data: Dict, prefix: str = "") -> Dict:
    """Recursively redact sensitive values in a dict."""
    result = {}
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            result[key] = _redact_dict(value, full_key)
        else:
            result[key] = _redact_value(full_key, value)
    return result


def _coerce_value(value: str) -> Any:
    """Coerce string value to appropriate type (int, float, bool, or string)."""
    if value.lower() in ('true', 'false'):
        return value.lower() == 'true'
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


class Config:
    def __init__(self, config_path: Optional[str] = None):
        self._data: Dict[str, Any] = {}
        if config_path:
            self.load(config_path)
        self._load_env_overrides()

    def load(self, path: str) -> None:
        with open(path) as f:
            self._data = json.load(f)

    def _load_env_overrides(self) -> None:
        prefix = "AO_"
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):].lower().replace("_", ".")
                self._set_nested(config_key, _coerce_value(value))

    def _set_nested(self, key: str, value: Any) -> None:
        parts = key.split(".")
        current = self._data
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value

    def get(self, key: str, default: Any = None) -> Any:
        parts = key.split(".")
        current = self._data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
                if current is None:
                    return default
            else:
                return default
        return current

    def set(self, key: str, value: Any) -> None:
        self._set_nested(key, value)

    def to_dict(self) -> Dict:
        return self._data

    def to_redacted_dict(self) -> Dict:
        """Return a redacted copy of the config with sensitive values masked.

        Keys matching sensitive patterns (password, secret, token, key,
        credential, auth, private, api_key, access_token, refresh_token)
        are replaced with '***REDACTED***'.

        Use this for diagnostic output and logs. Use to_dict() for
        trusted internal access.
        """
        return _redact_dict(self._data)
