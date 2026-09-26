"""
groq_provider.py
================
LLM provider for Groq with automatic multi-API-key rotation and failover.

Supports:
- GROQ_API_KEYS: comma-separated list of keys, e.g. "gsk_key1,gsk_key2"
- GROQ_API_KEY: single fallback key
- GROQ_API_KEY_1, GROQ_API_KEY_2, ...: numbered keys

When a rate limit (HTTP 429) or token exhaustion occurs, the client pool
automatically rotates to the next available key without changing the model.
The exact model ("openai/gpt-oss-120b") and temperature parameters are preserved.
"""

from __future__ import annotations

import os
import re
import time
from typing import Any
from dotenv import load_dotenv
from groq import Groq, RateLimitError

load_dotenv()


def load_groq_api_keys() -> list[str]:
    """
    Collect all Groq API keys from environment variables.
    Splits any comma-separated strings (in GROQ_API_KEYS, GROQ_API_KEY, etc.)
    and deduplicates keys while preserving order.
    """
    keys: list[str] = []

    # Check both GROQ_API_KEYS and GROQ_API_KEY
    for env_var in ["GROQ_API_KEYS", "GROQ_API_KEY"]:
        raw_val = os.getenv(env_var, "")
        if raw_val:
            for k in raw_val.split(","):
                k_clean = k.strip().strip('"').strip("'")
                if k_clean and k_clean not in keys:
                    keys.append(k_clean)

    # Numbered keys (GROQ_API_KEY_1, GROQ_API_KEY_2, ...)
    i = 1
    while True:
        k = os.getenv(f"GROQ_API_KEY_{i}")
        if not k:
            break
        for part in k.split(","):
            k_clean = part.strip().strip('"').strip("'")
            if k_clean and k_clean not in keys:
                keys.append(k_clean)
        i += 1

    return keys


class GroqClientPool:
    """
    Manages a pool of Groq API clients and automatically rotates through them
    upon encountering rate limits, quota exhaustion, or invalid keys.
    """

    def __init__(self, keys: list[str] | None = None) -> None:
        self.reload_keys(keys)

    def reload_keys(self, keys: list[str] | None = None) -> None:
        if keys is None:
            keys = load_groq_api_keys()
        self.keys = keys
        self.current_idx = 0
        self._clients: dict[int, Groq] = {}

    @property
    def total_keys(self) -> int:
        return len(self.keys)

    def get_client(self, idx: int | None = None) -> Groq:
        if not self.keys:
            raise EnvironmentError(
                "[Groq] No Groq API keys found. "
                "Please set GROQ_API_KEYS or GROQ_API_KEY in your .env file."
            )
        target_idx = self.current_idx if idx is None else idx
        if target_idx not in self._clients:
            self._clients[target_idx] = Groq(api_key=self.keys[target_idx])
        return self._clients[target_idx]

    def rotate_key(self, reason: str = "") -> int:
        if not self.keys:
            return 0
        old_idx = self.current_idx
        self.current_idx = (self.current_idx + 1) % len(self.keys)
        old_masked = f"...{self.keys[old_idx][-6:]}" if len(self.keys[old_idx]) > 6 else f"Key#{old_idx+1}"
        new_masked = f"...{self.keys[self.current_idx][-6:]}" if len(self.keys[self.current_idx]) > 6 else f"Key#{self.current_idx+1}"
        print(
            f"\n[Groq Rotation] Key #{old_idx + 1} ({old_masked}) rotated ({reason}). "
            f"Switching to Key #{self.current_idx + 1} ({new_masked}) [Pool size: {len(self.keys)}]."
        )
        return self.current_idx

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str = "openai/gpt-oss-120b",
        temperature: float = 0.2,
        max_tokens: int | None = None,
        max_retries: int = 4,
        **kwargs: Any,
    ) -> Any:
        if not self.keys:
            self.reload_keys()
            if not self.keys:
                raise EnvironmentError(
                    "[Groq] No Groq API keys found in environment. "
                    "Ensure GROQ_API_KEYS or GROQ_API_KEY is present in .env."
                )

        total_keys = len(self.keys)
        attempts = 0
        keys_tried_in_cycle = 0

        while attempts < max_retries * max(1, total_keys):
            attempts += 1
            client = self.get_client()

            call_args: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                **kwargs,
            }
            if max_tokens is not None:
                call_args["max_tokens"] = max_tokens

            try:
                return client.chat.completions.create(**call_args)

            except Exception as exc:
                err_str = str(exc)
                is_rate_limit = (
                    isinstance(exc, RateLimitError)
                    or "429" in err_str
                    or "rate_limit" in err_str.lower()
                    or "tokens" in err_str.lower()
                    or "quota" in err_str.lower()
                    or "resource_exhausted" in err_str.lower()
                )
                is_invalid_key = (
                    "401" in err_str
                    or "invalid_api_key" in err_str.lower()
                    or "invalid api key" in err_str.lower()
                )

                if is_rate_limit or is_invalid_key:
                    reason = "Invalid key (401)" if is_invalid_key else "Rate limit / tokens exhausted"
                    if total_keys > 1:
                        keys_tried_in_cycle += 1
                        self.rotate_key(reason=reason)

                        # If all keys in the pool have been rotated through in this cycle:
                        if keys_tried_in_cycle >= total_keys:
                            wait_sec = 6.0
                            wait_match = re.search(r"(?:try again in|retry[- ]after)\s*([0-9\.]+)\s*s?", err_str, re.IGNORECASE)
                            if wait_match:
                                try:
                                    wait_sec = max(2.0, float(wait_match.group(1)) + 1.0)
                                except ValueError:
                                    pass
                            print(
                                f"[Groq Rotation] All {total_keys} keys hit limits. "
                                f"Waiting {wait_sec:.1f}s for quota window to reset..."
                            )
                            time.sleep(wait_sec)
                            keys_tried_in_cycle = 0
                        continue
                    else:
                        wait_sec = 8.0
                        wait_match = re.search(r"(?:try again in|retry[- ]after)\s*([0-9\.]+)\s*s?", err_str, re.IGNORECASE)
                        if wait_match:
                            try:
                                wait_sec = max(2.0, float(wait_match.group(1)) + 1.0)
                            except ValueError:
                                pass
                        print(
                            f"[Groq] Limit/error hit on single key ({reason}). "
                            f"Waiting {wait_sec:.1f}s before retry... ({exc})"
                        )
                        time.sleep(wait_sec)
                        continue
                else:
                    print(f"[Groq] Error during completion: {exc}")
                    raise exc

        raise RuntimeError(
            f"[Groq] Exceeded maximum retries ({attempts}) across all available keys."
        )


# Global singleton pool
_GLOBAL_POOL = GroqClientPool()


def get_pool() -> GroqClientPool:
    return _GLOBAL_POOL


def chat_completion(*args: Any, **kwargs: Any) -> Any:
    """Helper to call chat_completion directly using the global rotating pool."""
    return _GLOBAL_POOL.chat_completion(*args, **kwargs)


def generate(prompt: str) -> str:
    """
    Main generate interface used by LexiClear (rag/llm.py, risk_analyzer.py, etc.).
    Preserves exact signature, prompt format, model, and temperature.
    """
    response = _GLOBAL_POOL.chat_completion(
        messages=[{"role": "user", "content": prompt}],
        model="openai/gpt-oss-120b",
        temperature=0.2,
    )
    return response.choices[0].message.content


# Backward compatibility if anything accesses client directly
class _ClientProxy:
    def __getattr__(self, name: str) -> Any:
        return getattr(_GLOBAL_POOL.get_client(), name)

client = _ClientProxy()