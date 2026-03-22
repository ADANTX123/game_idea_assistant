from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class RuntimeSettings:
    mode: str = "mock"
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4.1-mini"
    temperature: float = 0.4
    timeout_seconds: int = 25
    max_output_tokens: int = 1400

    def sanitized(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "base_url": self.base_url,
            "model": self.model,
            "temperature": self.temperature,
            "timeout_seconds": self.timeout_seconds,
            "max_output_tokens": self.max_output_tokens,
            "api_key_present": bool(self.api_key),
        }


class SettingsStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> RuntimeSettings:
        payload = self._load_payload()
        return RuntimeSettings(
            mode=self._read_string("GAME_IDEA_ASSISTANT_LLM_MODE", payload, "mode", "mock"),
            api_key=self._read_string("OPENAI_API_KEY", payload, "api_key", ""),
            base_url=self._read_string("OPENAI_BASE_URL", payload, "base_url", "https://api.openai.com/v1"),
            model=self._read_string("OPENAI_MODEL", payload, "model", "gpt-4.1-mini"),
            temperature=self._read_float("GAME_IDEA_ASSISTANT_TEMPERATURE", payload, "temperature", 0.4),
            timeout_seconds=self._read_int("GAME_IDEA_ASSISTANT_TIMEOUT_SECONDS", payload, "timeout_seconds", 25),
            max_output_tokens=self._read_int(
                "GAME_IDEA_ASSISTANT_MAX_OUTPUT_TOKENS",
                payload,
                "max_output_tokens",
                1400,
            ),
        )

    def save(self, updates: dict[str, Any]) -> RuntimeSettings:
        current = asdict(self.load())
        allowed = {
            "mode",
            "base_url",
            "model",
            "temperature",
            "timeout_seconds",
            "max_output_tokens",
        }
        for key, value in updates.items():
            if key in allowed:
                current[key] = value

        if updates.get("clear_api_key"):
            current["api_key"] = ""
        elif "api_key" in updates and str(updates["api_key"]).strip():
            current["api_key"] = str(updates["api_key"]).strip()

        settings = RuntimeSettings(
            mode=self._normalize_mode(current.get("mode", "mock")),
            api_key=str(current.get("api_key", "")).strip(),
            base_url=str(current.get("base_url", "https://api.openai.com/v1")).strip() or "https://api.openai.com/v1",
            model=str(current.get("model", "gpt-4.1-mini")).strip() or "gpt-4.1-mini",
            temperature=self._coerce_float(current.get("temperature", 0.4), 0.4),
            timeout_seconds=max(5, self._coerce_int(current.get("timeout_seconds", 25), 25)),
            max_output_tokens=max(200, self._coerce_int(current.get("max_output_tokens", 1400), 1400)),
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(asdict(settings), ensure_ascii=False, indent=2), encoding="utf-8")
        return settings

    def _load_payload(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def _read_string(self, env_key: str, payload: dict[str, Any], payload_key: str, default: str) -> str:
        env_value = os.getenv(env_key)
        if env_value is not None and env_value.strip():
            return env_value.strip()
        value = payload.get(payload_key, default)
        return str(value).strip() or default

    def _read_int(self, env_key: str, payload: dict[str, Any], payload_key: str, default: int) -> int:
        env_value = os.getenv(env_key)
        if env_value is not None and env_value.strip():
            return self._coerce_int(env_value, default)
        return self._coerce_int(payload.get(payload_key, default), default)

    def _read_float(self, env_key: str, payload: dict[str, Any], payload_key: str, default: float) -> float:
        env_value = os.getenv(env_key)
        if env_value is not None and env_value.strip():
            return self._coerce_float(env_value, default)
        return self._coerce_float(payload.get(payload_key, default), default)

    def _coerce_int(self, value: Any, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _coerce_float(self, value: Any, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _normalize_mode(self, mode: str) -> str:
        return "openai" if str(mode).strip().lower() == "openai" else "mock"
