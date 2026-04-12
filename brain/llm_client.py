import json
import os
from typing import Dict, Generator, Optional

import requests


class LLMClient:
    """
    Ollama tabanlı istemci.

    Hedef:
    - LLM'i ana açıklama motoru olarak kullanmak
    - intent / mode bazlı üretim derinliği sağlamak
    - deep modda daha zengin cevaplar üretmek
    - streaming'i korumak
    - keep_alive ile cold-start maliyetini azaltmak
    """

    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.url = f"{self.base_url}/api/generate"
        self.tags_url = f"{self.base_url}/api/tags"
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

        self.connect_timeout = int(os.getenv("OLLAMA_CONNECT_TIMEOUT", "10"))
        self.read_timeout = int(os.getenv("OLLAMA_READ_TIMEOUT", "240"))
        self.keep_alive = os.getenv("OLLAMA_KEEP_ALIVE", "20m")

        self.default_options: Dict[str, object] = {
            "temperature": float(os.getenv("OLLAMA_TEMPERATURE", "0.35")),
            "top_p": float(os.getenv("OLLAMA_TOP_P", "0.90")),
            "repeat_penalty": float(os.getenv("OLLAMA_REPEAT_PENALTY", "1.15")),
            "num_predict": int(os.getenv("OLLAMA_NUM_PREDICT", "220")),
            "num_ctx": int(os.getenv("OLLAMA_NUM_CTX", "4096")),
            "num_thread": int(os.getenv("OLLAMA_NUM_THREAD", "8")),
        }

    @property
    def model_name(self) -> str:
        return self.model

    # =========================================================
    # HEALTH / WARMUP
    # =========================================================
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
        Uygulama açılışında bir kez çağrılabilir.
        Modeli bellekte sıcak tutar.
        """
        try:
            payload = {
                "model": self.model,
                "prompt": "Hazır mısın?",
                "stream": False,
                "options": {
                    **self.default_options,
                    "num_predict": 8,
                    "temperature": 0.1,
                },
                "keep_alive": self.keep_alive,
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

    # =========================================================
    # GENERATE
    # =========================================================
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
            "keep_alive": self.keep_alive,
        }

        r = requests.post(
            self.url,
            json=payload,
            timeout=(self.connect_timeout, self.read_timeout),
        )
        r.raise_for_status()

        data = r.json()
        return (data.get("response") or "").strip()

    # =========================================================
    # STREAM
    # =========================================================
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
            "keep_alive": self.keep_alive,
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

    # =========================================================
    # OPTIONS
    # =========================================================
    def _build_options(
        self,
        mode: str = "balanced",
        override_options: Optional[Dict[str, object]] = None,
    ) -> Dict[str, object]:
        options = dict(self.default_options)

        # deterministic:
        # sabit, kısa, risksiz ve yüksek kontrol isteyen cevaplar
        if mode == "deterministic":
            options.update({
                "temperature": 0.12,
                "top_p": 0.78,
                "repeat_penalty": 1.20,
                "num_predict": 90,
            })

        # balanced:
        # normal eğitim / sohbet dengesi
        elif mode == "balanced":
            options.update({
                "temperature": 0.30,
                "top_p": 0.88,
                "repeat_penalty": 1.16,
                "num_predict": 220,
            })

        # deep:
        # açıklama, strateji, follow-up, detay, örnek
        elif mode == "deep":
            options.update({
                "temperature": 0.40,
                "top_p": 0.92,
                "repeat_penalty": 1.12,
                "num_predict": 360,
            })

        else:
            options.update({
                "temperature": 0.30,
                "top_p": 0.88,
                "repeat_penalty": 1.16,
                "num_predict": 220,
            })

        if override_options:
            options.update(override_options)

        return options
