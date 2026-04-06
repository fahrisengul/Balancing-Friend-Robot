import os
import re
import json
from typing import List, Tuple, Optional

import requests


class PoodleBrain:
    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
        self.model_name = os.getenv("OLLAMA_MODEL", "llama3")

        # Memory injection disiplinini korumak için üst sınırlar
        self.max_memories = 3
        self.max_memory_chars = 420

        # Sık bozuk STT örnekleri / zayıf girişler
        self.low_confidence_patterns = [
            r"^[a-zçğıöşü]{1,4}\.?$",
            r"^(sultan|koday bilir|yakın saknı demek|aba|baba|tamam|peki|hmm)\.?$",
        ]

        self.system_prompt = """
Sen Poodle'sın. Sıcak, doğal, zeki ve güven veren bir masaüstü robot arkadaşsın.
Tanem ile konuşurken samimi ama ölçülü olursun. Karikatürize, aşırı şirin, anlamsız veya yapay konuşmazsın.

TEMEL KURALLAR
1. Her zaman Türkçe konuş.
2. Kısa, doğal ve insana yakın cevap ver.
3. Önce kullanıcının son cümlesine doğrudan cevap ver.
4. Kullanıcı sormadıysa alakasız konu açma.
5. Aynı bilgileri tekrar tekrar söyleme.
6. "Doğum günü", "30 Mayıs", "voleybol", "robot kulübü" gibi bilgileri sadece gerçekten ilgiliyse kullan.
7. Uydurma detay üretme.
8. Kullanıcıyı yanlış anladıysan bunu dürüstçe söyle.
9. Çok bozuk veya belirsiz girdilerde cevap uydurma; kısa bir açıklama iste.
10. Her yanıt en fazla 2-3 cümle olsun. Gereksiz uzatma yapma.

ÜSLUP
- Doğal konuş.
- İnsan gibi kısa dönütler ver.
- Robot gibi mekanik değil, ama saçma ve teatral de değil.
- Gerekirse karşı soru sor, ama her cevapta soru sorma.

YASAKLAR
- Her cevabı Tanem'in doğum gününe bağlama.
- Her cevabı duygusal veya dramatik yapma.
- Anlamsız STT çıktısına özgüvenli cevap üretme.
- Aynı özel bilgiyi sürekli tekrar etme.
""".strip()

    # ---------------------------------------------------------
    # PUBLIC API
    # ---------------------------------------------------------
    def ask_poodle(self, user_text: str) -> str:
        user_text = (user_text or "").strip()
        if not user_text:
            return "Seni duydum ama bir şey anlayamadım. Tekrar söyler misin?"

        if self._needs_clarification(user_text):
            return self._clarification_response(user_text)

        memories = self._retrieve_relevant_memories(user_text)
        prompt = self._build_prompt(user_text, memories)

        try:
            raw = self._call_ollama(prompt)
            answer = self._postprocess_answer(raw, user_text)
            return answer
        except Exception:
            return "Şu an cevap üretirken küçük bir sorun yaşadım. Bir daha söyler misin?"

    # ---------------------------------------------------------
    # CLARIFICATION GATE
    # ---------------------------------------------------------
    def _needs_clarification(self, text: str) -> bool:
        normalized = self._normalize(text)

        if len(normalized) < 3:
            return True

        for pat in self.low_confidence_patterns:
            if re.match(pat, normalized):
                return True

        tokens = normalized.split()
        if len(tokens) == 1:
            weak_words = {
                "sultan", "tamam", "peki", "hmm", "hey", "evet", "yok", "şey", "bilemedim"
            }
            if tokens[0] in weak_words:
                return True

        # içinde fiil/soru izi olmayan garip transkriptler
        if len(tokens) >= 2:
            weak_signals = ["mi", "mı", "mu", "mü", "nasıl", "neden", "ne", "kim", "hangi", "yaptın", "oldu"]
            if not any(ws in normalized for ws in weak_signals) and len(tokens) <= 2:
                if all(len(t) <= 6 for t in tokens):
                    return True

        return False

    def _clarification_response(self, text: str) -> str:
        return "Seni tam anlayamadım. Son cümleni biraz daha net tekrar eder misin?"

    # ---------------------------------------------------------
    # MEMORY DISCIPLINE
    # ---------------------------------------------------------
    def _retrieve_relevant_memories(self, query: str) -> List[str]:
        """
        memory_manager API'si repo içinde değişebilir.
        Bu yüzden yumuşak entegrasyon yapıyoruz.
        """
        try:
            from memory_manager import MemoryManager  # type: ignore
        except Exception:
            return []

        try:
            mm = MemoryManager()
        except Exception:
            return []

        candidates = []

        # Farklı olası method isimlerini destekle
        for method_name in ["search_memories", "search", "query_memories", "retrieve_relevant"]:
            if hasattr(mm, method_name):
                method = getattr(mm, method_name)
                try:
                    result = method(query)
                    candidates = self._normalize_memory_results(result)
                    break
                except Exception:
                    continue

        if not candidates:
            return []

        # Basit relevance filtreleme
        query_tokens = set(self._normalize(query).split())
        scored = []

        for mem in candidates:
            mem_norm = self._normalize(mem)
            mem_tokens = set(mem_norm.split())
            overlap = len(query_tokens.intersection(mem_tokens))

            # sadece gerçekten ilişkili olanları geçir
            if overlap == 0:
                continue

            # doğum günü / sabit persona spam'ini baskıla
            penalty = 0
            for repetitive in ["30 mayis", "dogum gunu", "voleybol", "robot kulubu"]:
                if repetitive in mem_norm and repetitive not in self._normalize(query):
                    penalty += 1

            score = overlap - penalty
            if score > 0:
                scored.append((score, mem))

        scored.sort(key=lambda x: x[0], reverse=True)
        selected = [m for _, m in scored[: self.max_memories]]

        compact = []
        total_chars = 0
        for mem in selected:
            cleaned = mem.strip()
            if not cleaned:
                continue
            if total_chars + len(cleaned) > self.max_memory_chars:
                break
            compact.append(cleaned)
            total_chars += len(cleaned)

        return compact

    def _normalize_memory_results(self, result) -> List[str]:
        if result is None:
            return []

        if isinstance(result, str):
            return [result]

        if isinstance(result, list):
            out = []
            for item in result:
                if isinstance(item, str):
                    out.append(item)
                elif isinstance(item, dict):
                    for key in ["text", "content", "memory", "value"]:
                        if key in item and isinstance(item[key], str):
                            out.append(item[key])
                            break
            return out

        return []

    # ---------------------------------------------------------
    # PROMPT BUILDING
    # ---------------------------------------------------------
    def _build_prompt(self, user_text: str, memories: List[str]) -> str:
        memory_block = ""
        if memories:
            memory_lines = "\n".join(f"- {m}" for m in memories)
            memory_block = f"""
İLGİLİ HAFIZA (yalnızca gerçekten işe yarıyorsa kullan, zorla kullanma):
{memory_lines}
""".strip()

        return f"""
{self.system_prompt}

{memory_block}

KULLANICI MESAJI:
{user_text}

GÖREV:
- Kullanıcının son cümlesine doğal ve kısa cevap ver.
- Hafızayı sadece gerçekten ilgiliyse kullan.
- Emin değilsen dürüst ol.
- Tekrara düşme.
- Çıktı sadece nihai cevap olsun.
""".strip()

    # ---------------------------------------------------------
    # LLM CALL
    # ---------------------------------------------------------
    def _call_ollama(self, prompt: str) -> str:
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.65,
                "top_p": 0.9,
                "repeat_penalty": 1.18,
                "num_predict": 120,
            },
        }

        resp = requests.post(self.ollama_url, json=payload, timeout=90)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "").strip()

    # ---------------------------------------------------------
    # POSTPROCESS
    # ---------------------------------------------------------
    def _postprocess_answer(self, text: str, user_text: str) -> str:
        answer = (text or "").strip()

        if not answer:
            return "Bunu duyduğuma sevindim. Bir kez daha söyler misin?"

        # tek satır ve kısa tut
        answer = re.sub(r"\s+", " ", answer).strip()

        # model bazen prompt tekrarlar
        banned_prefixes = [
            "kullanıcı mesajı:",
            "görev:",
            "ilgili hafıza:",
        ]
        for bp in banned_prefixes:
            if answer.lower().startswith(bp):
                return "Bunu tam düzgün çıkaramadım. Son cümleni tekrar eder misin?"

        # Çok uzun yanıtları buda
        sentences = re.split(r"(?<=[.!?])\s+", answer)
        answer = " ".join(sentences[:3]).strip()

        # Bozuk tekrarlar
        repetitive_phrases = [
            "30 mayıs", "doğum günün", "voleybol", "robot kulübü"
        ]
        if self._normalize(user_text).find("doğum") == -1:
            hits = sum(1 for p in repetitive_phrases if p in self._normalize(answer))
            if hits >= 2:
                return "Anladım. Bunu biraz daha sade söyleyeyim: ne demek istediğini biraz açar mısın?"

        return answer

    # ---------------------------------------------------------
    # UTILS
    # ---------------------------------------------------------
    def _normalize(self, text: str) -> str:
        t = text.lower().strip()
        t = (
            t.replace("ı", "i")
             .replace("ğ", "g")
             .replace("ş", "s")
             .replace("ç", "c")
             .replace("ö", "o")
             .replace("ü", "u")
        )
        t = re.sub(r"[^a-z0-9\s]", " ", t)
        t = re.sub(r"\s+", " ", t).strip()
        return t
