from __future__ import annotations

import os


class LLMClient:
    def __init__(self, provider: str, model: str) -> None:
        self.provider = provider
        self.model = model

    def summarize(self, prompt: str) -> str:
        if self.provider != "openai":
            raise ValueError(f"Unsupported provider: {self.provider}")

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")

        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=self.model,
            input=prompt,
        )
        return (response.output_text or "").strip()

