from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


class LMStudioError(RuntimeError):
    pass


@dataclass(frozen=True)
class ModelInfo:
    identifier: str
    owned_by: str = ""


class LMStudioClient:
    def __init__(self, endpoint: str, api_key: str = "", timeout_seconds: float = 10.0) -> None:
        self.endpoint = self._normalize_endpoint(endpoint)
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def _normalize_endpoint(endpoint: str) -> str:
        normalized = endpoint.strip().rstrip("/")
        if not normalized:
            normalized = "http://127.0.0.1:1234/v1"
        elif not normalized.endswith("/v1"):
            normalized = normalized + "/v1"

        return normalized + "/"

    def list_models(self) -> list[ModelInfo]:
        payload = self._request_json("models")
        models = payload.get("data", [])
        return [
            ModelInfo(identifier=item.get("id", ""), owned_by=item.get("owned_by", ""))
            for item in models
            if item.get("id")
        ]

    def chat(self, user_message: str, model: str) -> str:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": user_message}],
        }
        response = self._request_json("chat/completions", payload)

        try:
            return response["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise LMStudioError("LM Studio returned an unexpected response format.") from exc

    def _request_json(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = urljoin(self.endpoint, path)
        headers = {"Content-Type": "application/json"}

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        body = None
        method = "GET"
        if payload is not None:
            method = "POST"
            body = json.dumps(payload).encode("utf-8")

        request = Request(url=url, data=body, headers=headers, method=method)

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise LMStudioError(f"LM Studio request failed with status {exc.code}: {details}") from exc
        except URLError as exc:
            raise LMStudioError(f"Unable to reach LM Studio at {self.endpoint}.") from exc

        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LMStudioError("LM Studio returned invalid JSON.") from exc