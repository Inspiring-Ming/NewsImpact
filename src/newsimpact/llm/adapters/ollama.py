"""LlmProvider for local models served by Ollama (https://ollama.com).

Runs on your own machine or server: no per-token cost, no data leaves the
machine. Ollama constrains the answer to our JSON schema ("format").
Quality depends on the model you pull - compare it with `newsimpact evaluate`.
"""

from __future__ import annotations

import json

import httpx

from newsimpact.llm.models import LlmReply, LlmRequest


class OllamaProvider:
    def __init__(self, model: str, client: httpx.Client, base_url: str) -> None:
        self._model = model
        self._client = client
        self._url = base_url.rstrip("/") + "/api/chat"
        self.name = f"ollama:{model}"

    def complete(self, request: LlmRequest) -> LlmReply:
        resp = self._client.post(self._url, json={
            "model": self._model,
            "messages": [{"role": "system", "content": request.system},
                         {"role": "user", "content": request.prompt}],
            "format": request.schema_,
            "stream": False,
            "options": {"temperature": 0, "num_predict": request.max_output_tokens},
        })  # fmt: skip
        resp.raise_for_status()
        body = resp.json()
        try:
            data = json.loads(body["message"]["content"])
        except (KeyError, json.JSONDecodeError):
            data = None
        return LlmReply(data=data, model=f"ollama:{self._model}",
                        input_tokens=int(body.get("prompt_eval_count", 0)),
                        output_tokens=int(body.get("eval_count", 0)))  # fmt: skip
