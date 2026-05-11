import json
import unittest
from unittest.mock import patch

from src.lm_studio_client import LMStudioClient, LMStudioError


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class LMStudioClientTests(unittest.TestCase):
    def test_endpoint_is_normalized_when_v1_is_missing(self) -> None:
        client = LMStudioClient("http://127.0.0.1:1234")

        self.assertEqual(client.endpoint, "http://127.0.0.1:1234/v1/")

    @patch("src.lm_studio_client.urlopen")
    def test_list_models_parses_response(self, mock_urlopen) -> None:
        mock_urlopen.return_value = FakeResponse({"data": [{"id": "model-a", "owned_by": "lm-studio"}]})
        client = LMStudioClient("http://127.0.0.1:1234/v1")

        models = client.list_models()

        self.assertEqual(len(models), 1)
        self.assertEqual(models[0].identifier, "model-a")

    @patch("src.lm_studio_client.urlopen")
    def test_chat_returns_content(self, mock_urlopen) -> None:
        mock_urlopen.return_value = FakeResponse(
            {"choices": [{"message": {"content": "hello from model"}}]}
        )
        client = LMStudioClient("http://127.0.0.1:1234/v1")

        response = client.chat("hello", "model-a")

        self.assertEqual(response, "hello from model")

    @patch("src.lm_studio_client.urlopen")
    def test_chat_raises_for_invalid_shape(self, mock_urlopen) -> None:
        mock_urlopen.return_value = FakeResponse({"choices": []})
        client = LMStudioClient("http://127.0.0.1:1234/v1")

        with self.assertRaises(LMStudioError):
            client.chat("hello", "model-a")


if __name__ == "__main__":
    unittest.main()