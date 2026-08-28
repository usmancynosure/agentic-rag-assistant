"""LLM client abstraction and Anthropic (Claude) implementation.

An ``LLMClient`` protocol decouples callers from the provider. The Anthropic
implementation uses the Messages API with adaptive thinking and returns the
concatenated text blocks. The underlying client is injectable so tests need
neither an API key nor the SDK.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from app.core.logging import get_logger

logger = get_logger(__name__)


@runtime_checkable
class LLMClient(Protocol):
    def generate(self, *, system: str, prompt: str, max_tokens: int) -> str: ...


class AnthropicLLM:
    def __init__(self, *, api_key: str, model: str, client: Any | None = None) -> None:
        self._api_key = api_key
        self._model = model
        self._client = client

    def _get_client(self) -> Any:
        if self._client is None:
            import anthropic  # lazy

            self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client

    def generate(self, *, system: str, prompt: str, max_tokens: int) -> str:
        response = self._get_client().messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            thinking={"type": "adaptive"},
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        )
        logger.info("llm_generate", model=self._model, chars=len(text))
        return text
