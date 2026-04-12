import os
import json
import requests


class LLMClient:
    def __init__(self):
        self.url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

    def generate(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "top_p": 0.8,
                "repeat_penalty": 1.15,
                "num_predict": 60,
            },
        }

        r = requests.post(self.url, json=payload, timeout=60)
        r.raise_for_status()
        return r.json().get("response", "").strip()

    def stream(self, prompt: str):
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": 0.2,
                "top_p": 0.8,
                "repeat_penalty": 1.15,
                "num_predict": 60,
            },
        }

        with requests.post(self.url, json=payload, stream=True, timeout=120) as r:
            r.raise_for_status()

            for line in r.iter_lines(decode_unicode=True):
                if not line:
                    continue

                try:
                    data = json.loads(line)
                except Exception:
                    continue

                chunk = data.get("response", "")
                if chunk:
                    yield chunk

                if data.get("done"):
                    break
