import json
import os
import time
from typing import Dict, Generator, Optional

import requests


class LLMClient:
    """
    Ollama tabanlı üretim istemcisi.

    Tasarım hedefleri:
    - LLM'i gerçekten aktif kullanmak
    - RAG bağlamı varken daha kaliteli ve daha derin cevap vermek
    - streaming'i korumak
    - model warm tutarak gereksiz cold-start maliyetini azaltmak
    """

    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.url = f"{self.base_url}/api/generate"
        self.tags_url = f"{self.base_url}/api/tags"
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

        # latency / kalite dengesi
        self.default_options: Dict[str, object] = {
            "temperature": float(os.getenv("OLLAMA_TEMPERATURE", "0.35")),
            "top_p": float(os.getenv("OLLAMA_TOP_P", "0.9")),
            "repeat_penalty": float(os.getenv("OLLAMA_REPEAT_PENALTY", "1.18")),
            "num_predict": int(os.getenv("OLLAMA_NUM_PREDICT", "220")),
            "num_ctx": int(os.getenv("OLLAMA_NUM_CTX", "4096")),
            "num_thread": int(os.getenv("OLLAMA_NUM_THREAD", "8")),
        }

        self.connect_timeout = int(os.getenv("OLLAMA_CONNECT_TIMEOUT", "10"))
        self.read_timeout = int(os.getenv("OLLAMA_READ_TIMEOUT", "180"))

    @property
    def model_name(self) -> str:
        return self.model

    def healthcheck(self) -> bool:
        try:
            r = requests.get(
                self.tags_url,
                timeout=(self.connect_timeout, 20),
            )
            r.raise_for_status()
            return True
        except Exception:
            return False

    def warmup(self) -> bool:
        """
        Modeli bellekte sıcak tutmak için hafif bir çağrı.
        İstersen uygulama açılışında bir kez çalıştır.
        """
        try:
            payload = {
                "model": self.model,
                "prompt": "Hazır mısın?",
                "stream": False,
                "options": {
                    **self.default_options,
                    "num_predict": 5,
                },
                "keep_alive": "15m",
            }
            r = requests.post(
                self.url,
                json=payload,
                timeout=(self.connect_timeout, 60),
            )
            r.raise_for_status()
            return True
        except Exception:
            return False

    def generate(
        self,
        prompt: str,
        mode: str = "balanced",
        override_options: Optional[Dict[str, object]] = None,
    ) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": self._build_options(mode=mode, override_options=override_options),
            "keep_alive": "15m",
        }

        r = requests.post(
            self.url,
            json=payload,
            timeout=(self.connect_timeout, self.read_timeout),
        )
        r.raise_for_status()

        data = r.json()
        return (data.get("response") or "").strip()

    def stream(
        self,
        prompt: str,
        mode: str = "balanced",
        override_options: Optional[Dict[str, object]] = None,
    ) -> Generator[str, None, None]:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": self._build_options(mode=mode, override_options=override_options),
            "keep_alive": "15m",
        }

        with requests.post(
            self.url,
            json=payload,
            stream=True,
            timeout=(self.connect_timeout, self.read_timeout),
        ) as r:
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

    def _build_options(
        self,
        mode: str = "balanced",
        override_options: Optional[Dict[str, object]] = None,
    ) -> Dict[str, object]:
        options = dict(self.default_options)

        # Strateji:
        # - deterministic: sabit / net / doğru cevaplar
        # - balanced: normal eğitim ve açıklama akışı
        # - deep: daha detaylı ama kontrollü cevaplar
        if mode == "deterministic":
            options.update({
                "temperature": 0.15,
                "top_p": 0.80,
                "repeat_penalty": 1.20,
                "num_predict": 140,
            })
        elif mode == "deep":
            options.update({
                "temperature": 0.45,
                "top_p": 0.92,
                "repeat_penalty": 1.15,
                "num_predict": 320,
            })
        else:  # balanced
            options.update({
                "temperature": 0.35,
                "top_p": 0.90,
                "repeat_penalty": 1.18,
                "num_predict": 220,
            })

        if override_options:
            options.update(override_options)

        return options
