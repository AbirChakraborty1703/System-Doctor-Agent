"""Optional LLM provider wrapper with deterministic fallback behavior."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .config import AppConfig
from .logger import get_logger


@dataclass
class LLMResult:
    text: str
    provider_used: str
    fallback_used: bool


class LLMProvider:
    """Provider abstraction for OpenAI, Gemini, or deterministic fallback."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._logger = get_logger("systemdoctor.llm")

    def complete(self, system_prompt: str, user_prompt: str, fallback_fn: Callable[[], str]) -> LLMResult:
        provider = self.config.llm_provider

        if provider == "openai" and self.config.openai_api_key:
            text = self._complete_openai(system_prompt, user_prompt)
            if text:
                return LLMResult(text=text, provider_used="openai", fallback_used=False)

        if provider == "gemini" and self.config.gemini_api_key:
            text = self._complete_gemini(system_prompt, user_prompt)
            if text:
                return LLMResult(text=text, provider_used="gemini", fallback_used=False)

        return LLMResult(text=fallback_fn(), provider_used="fallback", fallback_used=True)

    def _complete_openai(self, system_prompt: str, user_prompt: str) -> str:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.config.openai_api_key)
            response = client.chat.completions.create(
                model=self.config.openai_model,
                temperature=0.2,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            content = response.choices[0].message.content
            return content.strip() if content else ""
        except Exception as exc:  # pragma: no cover
            self._logger.warning("openai completion failed: %s", exc)
            return ""

    def _complete_gemini(self, system_prompt: str, user_prompt: str) -> str:
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.config.gemini_api_key)
            model = genai.GenerativeModel(self.config.gemini_model)
            response = model.generate_content(
                [
                    {"role": "user", "parts": [system_prompt]},
                    {"role": "user", "parts": [user_prompt]},
                ]
            )
            text = getattr(response, "text", "")
            return text.strip() if text else ""
        except Exception as exc:  # pragma: no cover
            self._logger.warning("gemini completion failed: %s", exc)
            return ""
