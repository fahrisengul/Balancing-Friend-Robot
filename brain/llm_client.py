import os
import requests


class LLMClient:
    def __init__(self):
        self.url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
        self.model = os.getenv("OLLAMA_MODEL", "llama3")

    def generate(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "top_p": 0.8,
                "repeat_penalty": 1.2,
                "num_predict": 80,
            },
        }

        r = requests.post(self.url, json=payload, timeout=60)
        r.raise_for_status()
        return r.json().get("response", "").strip()
