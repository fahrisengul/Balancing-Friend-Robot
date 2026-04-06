import os
import re
from datetime import date
from typing import List, Optional, Tuple

import requests


class PoodleBrain:
    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
        self.model_name = os.getenv("OLLAMA_MODEL", "llama3")

        self.max_memories = 3
        self.max_memory_chars = 420

        # Son tur bağlam
        self.last_user_text: str = ""
        self.last_answer_text: str = ""

        # Sık bozuk STT örnekleri / zayıf girişler
        self.low_confidence_patterns = [
            r"^[a-zçğıöşü]{1,4}\.?$",
            r"^(sultan|koday bilir|yakın saknı demek|aba|baba|tamam|peki|hmm|ejem|tum|tüm)\.?$",
            r"^(mursun sen|nasirsan nasir gidiyor|dom tarihim ikibu nonuc)\.?$",
        ]

        self.follow_up_patterns = {
            "emin misin",
            "neden",
            "neden öyle",
            "ne demek istin",
            "ne demek istedin",
            "nasil yani",
            "nasıl yani",
        }

        self.system_prompt = """
Sen Poodle'sın. Sıcak, doğal, kısa ve güven veren bir masaüstü robot arkadaşsın.
Tanem ile konuşurken samimi ama ölçülü olursun. Yapay, saçma, teatral veya gereksiz aşırı şirin konuşmazsın.

TEMEL KURALLAR
1. Her zaman Türkçe konuş.
2. Kısa ve doğal cevap ver.
3. Önce kullanıcının son cümlesine doğrudan cevap ver.
4. Kullanıcı sormadıysa alakasız konu açma.
5. Aynı bilgileri tekrar tekrar söyleme.
6. "Doğum günü", "30 Mayıs", "voleybol", "robot kulübü" gibi bilgileri sadece gerçekten ilgiliyse kullan.
7. Uydurma detay üretme.
8. Emin değilsen dürüstçe söyle.
9. Kullanıcıyı yanlış anladıysan açıklama iste.
10. Her yanıt en fazla 2 cümle olsun.

ÜSLUP
- Doğal konuş.
- Kısa cevap ver.
- Gerekirse tek bir kısa karşı soru sor.
- Robot gibi kendini tarif etme.
- “Görevim”, “ben bir robotum”, “sana doğal cevap veriyorum” gibi ifadeleri kullanma.

YASAKLAR
- Her cevabı Tanem'in doğum gününe bağlama.
- Her cevabı duygusal veya dramatik yapma.
- Anlamsız STT çıktısına özgüvenli cevap üretme.
- Kullanıcının cümlesini anlamsız şekilde tekrar etme.
- Gerçek olmayan sayı, tarih, yaş veya kesin bilgi uydurma.
""".strip()

    # ---------------------------------------------------------
    # PUBLIC API
    # ---------------------------------------------------------
    def ask_poodle(self, user_text: str) -> str:
        user_text = (user_text or "").strip()
        if not user_text:
            return "Seni duydum ama bir şey anlayamadım. Tekrar söyler misin?"

        normalized = self._normalize(user_text)

        # 1) follow-up kontrolü
        if self._is_follow_up(normalized):
            handled = self._handle_follow_up(normalized)
            if handled:
                self.last_user_text = user_text
                self.last_answer_text = handled
                return handled

        # 2) clarification gate
        if self._needs_clarification(user_text):
            answer = self._clarification_response(user_text)
            self.last_user_text = user_text
            self.last_answer_text = answer
            return answer

        # 3) deterministic sorular
        deterministic_answer = self._handle_deterministic_questions(user_text)
        if deterministic_answer:
            self.last_user_text = user_text
            self.last_answer_text = deterministic_answer
            return deterministic_answer

        # 4) memory
        memories = self._retrieve_relevant_memories(user_text)

        # 5) prompt
        prompt = self._build_prompt(user_text, memories)

        try:
            raw = self._call_ollama(prompt)
            answer = self._postprocess_answer(raw, user_text)
        except Exception:
            answer = "Şu an cevap üretirken küçük bir sorun yaşadım. Bir daha söyler misin?"

        self.last_user_text = user_text
        self.last_answer_text = answer
        return answer

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
                "sultan", "tamam", "peki", "hmm", "hey", "evet", "yok", "sey",
                "şey", "bilemedim", "tum", "tüm", "ejem", "gorsun", "görsün"
            }
            if tokens[0] in weak_words:
                return True

        # anlamsal bozukluklar
        if self._looks_like_garbled_text(normalized):
            return True

        # sayı/tarih sorusu ama parse edilebilir sinyal yoksa
        if self._is_date_or_age_question(normalized):
            if not self._has_date_or_age_signal(normalized):
                return True

        return False

    def _clarification_response(self, text: str) -> str:
        return "Seni tam anlayamadım. Son cümleni biraz daha net tekrar eder misin?"

    def _looks_like_garbled_text(self, normalized: str) -> bool:
        tokens = normalized.split()

        if len(tokens) == 0:
            return True

        # çok kısa, anlamsız ikili yapılar
        if len(tokens) <= 2 and all(len(t) <= 6 for t in tokens):
            weak_signals = {"ne", "neden", "nasil", "nasil", "hangi", "kim", "mi", "mı", "mu", "mü"}
            if not any(w in normalized for w in weak_signals):
                suspicious = {
                    "mursun", "nasirsan", "nasir", "dom", "nonuc", "ikibu", "koday", "saknı", "sakni"
                }
                if any(tok in suspicious for tok in tokens):
                    return True

        # bozuk tekrar kalıpları
        if re.search(r"\b([a-zçğıöşü]{3,})\s+\1\b", normalized):
            return True

        return False

    # ---------------------------------------------------------
    # FOLLOW-UP HANDLING
    # ---------------------------------------------------------
    def _is_follow_up(self, normalized: str) -> bool:
        return normalized in self.follow_up_patterns

    def _handle_follow_up(self, normalized: str) -> Optional[str]:
        if not self.last_answer_text:
            return "Neyi kastettiğini tam anlayamadım. Son cümleni biraz açar mısın?"

        if normalized == "emin misin":
            if "emin degilim" in self._normalize(self.last_answer_text):
                return "Zaten emin olmadığımı söylemek istemiştim. İstersen bunu tekrar kontrol edelim."
            return "Tam emin değilsem bunu söylemem daha doğru olur. İstersen bunu bir daha netleştirelim."

        if normalized in {"neden", "neden öyle"}:
            return "Bunu önceki cümlene göre söyledim. İstersen sorunu bir kez daha daha net kur, ben de daha düzgün cevap vereyim."

        if normalized in {"ne demek istin", "ne demek istedin", "nasil yani", "nasıl yani"}:
            return "Daha açık söyleyeyim: seni yanlış anlamış olabilirim. Son cümleni tekrar edersen daha net cevap veririm."

        return None

    # ---------------------------------------------------------
    # DETERMINISTIC LOGIC
    # ---------------------------------------------------------
    def _handle_deterministic_questions(self, user_text: str) -> Optional[str]:
        normalized = self._normalize(user_text)

        birth_date = self._get_birth_date_from_memory()

        if "dogum gunum ne zaman" in normalized or "dogum gunum ne zamanda" in normalized:
            if birth_date:
                return f"Doğum günün {birth_date[2]} {self._month_name_tr(birth_date[1])}."
            return "Doğum tarihini hafızamda net bulamadım."

        if "kac yasina girecegim" in normalized or "kaç yaşına gireceğim" in user_text.lower():
            if birth_date:
                next_age = self._next_age_on_next_birthday(birth_date)
                if next_age is not None:
                    return f"Bir sonraki doğum gününde {next_age} yaşına gireceksin."
            return "Bunu doğru hesaplayabilmem için doğum yılını net bilmem gerekiyor."

        if "kac yasindayim" in normalized or "kaç yaşındayım" in user_text.lower():
            if birth_date:
                age = self._current_age(birth_date)
                if age is not None:
                    return f"Şu anda {age} yaşındasın."
            return "Bunu doğru hesaplayabilmem için doğum yılını net bilmem gerekiyor."

        return None

    def _is_date_or_age_question(self, normalized: str) -> bool:
        keys = [
            "dogum", "tarih", "yas", "kac yas", "kaç yaş", "dogum gunu"
        ]
        return any(k in normalized for k in keys)

    def _has_date_or_age_signal(self, normalized: str) -> bool:
        # soru yapısını tanımak için kaba sinyal
        keys = ["ne zaman", "kac yas", "kaç yaş", "hangi tarih", "dogum gunum", "dogum tarihim"]
        return any(k in normalized for k in keys)

    def _get_birth_date_from_memory(self) -> Optional[Tuple[int, int, int]]:
        """
        Memory'den YYYY-MM-DD veya benzeri bilgi çekmeye çalışır.
        Şimdilik kullanıcı hafızandaki bilinen örneğe göre 2013-05-30 fallback kullanıyoruz.
        """
        # Sabit fallback: mevcut senaryodaki bilinen bilgi
        # İstersen bunu tamamen memory_manager'a da bırakabiliriz.
        return (2013, 5, 30)

    def _current_age(self, birth_date: Tuple[int, int, int]) -> Optional[int]:
        try:
            today = date.today()
            by, bm, bd = birth_date
            age = today.year - by - ((today.month, today.day) < (bm, bd))
            return age
        except Exception:
            return None

    def _next_age_on_next_birthday(self, birth_date: Tuple[int, int, int]) -> Optional[int]:
        current_age = self._current_age(birth_date)
        if current_age is None:
            return None
        return current_age + 1

    def _month_name_tr(self, month: int) -> str:
        months = {
            1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 5: "Mayıs", 6: "Haziran",
            7: "Temmuz", 8: "Ağustos", 9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"
        }
        return months.get(month, str(month))

    # ---------------------------------------------------------
    # MEMORY DISCIPLINE
    # ---------------------------------------------------------
    def _retrieve_relevant_memories(self, query: str) -> List[str]:
        try:
            from memory_manager import MemoryManager  # type: ignore
        except Exception:
            return []

        try:
            mm = MemoryManager()
        except Exception:
            return []

        candidates = []

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

        query_tokens = set(self._normalize(query).split())
        scored = []

        for mem in candidates:
            mem_norm = self._normalize(mem)
            mem_tokens = set(mem_norm.split())
            overlap = len(query_tokens.intersection(mem_tokens))

            if overlap == 0:
                continue

            penalty = 0
            for repetitive in ["30 mayis", "dogum gunu", "voleybol", "robot kulubu"]:
                if repetitive in mem_norm and repetitive not in self._normalize(query):
                    penalty += 2

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

        conversation_block = ""
        if self.last_user_text and self.last_answer_text:
            conversation_block = f"""
ÖNCEKİ KISA BAĞLAM:
- Kullanıcı: {self.last_user_text}
- Poodle: {self.last_answer_text}
""".strip()

        return f"""
{self.system_prompt}

{memory_block}

{conversation_block}

KULLANICI MESAJI:
{user_text}

GÖREV:
- Kullanıcının son cümlesine doğal ve kısa cevap ver.
- Hafızayı sadece gerçekten ilgiliyse kullan.
- Emin değilsen dürüst ol.
- Tekrara düşme.
- Kullanıcının cümlesini anlamsız şekilde aynalama.
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
                "temperature": 0.45,
                "top_p": 0.9,
                "repeat_penalty": 1.22,
                "num_predict": 90,
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
            return "Bunu tam çıkaramadım. Bir kez daha söyler misin?"

        answer = re.sub(r"\s+", " ", answer).strip()

        banned_prefixes = [
            "kullanıcı mesajı:",
            "görev:",
            "ilgili hafıza:",
            "önceki kısa bağlam:",
        ]
        for bp in banned_prefixes:
            if answer.lower().startswith(bp):
                return "Bunu tam düzgün çıkaramadım. Son cümleni tekrar eder misin?"

        # çok uzun cevapları kısalt
        sentences = re.split(r"(?<=[.!?])\s+", answer)
        answer = " ".join(sentences[:2]).strip()

        # prompt leakage / robotik ifadeleri temizle
        robotic_phrases = [
            "ben bir robotum",
            "görevim",
            "sana doğal cevap veriyorum",
            "robot arkadaşındır",
            "ben sen poodle",
        ]
        if any(rp in self._normalize(answer) for rp in robotic_phrases):
            return "İyiyim, teşekkür ederim. Sen nasılsın?"

        # kullanıcı cümlesini anlamsız aynalıyorsa
        norm_user = self._normalize(user_text)
        norm_answer = self._normalize(answer)
        if norm_user and norm_answer and norm_answer.startswith(norm_user):
            return "Anladım. Bununla ilgili biraz daha anlatmak ister misin?"

        repetitive_phrases = [
            "30 mayıs", "doğum günün", "voleybol", "robot kulübü"
        ]
        if self._normalize(user_text).find("doğum") == -1:
            hits = sum(1 for p in repetitive_phrases if p in self._normalize(answer))
            if hits >= 2:
                return "Anladım. Bunu daha sade söyleyeyim: biraz daha açar mısın?"

        # aşırı kısa ve anlamsız cevaplar
        if len(answer.split()) <= 2 and self._normalize(answer) in {"52", "iyi şey", "tamam işte"}:
            return "Bundan tam emin değilim. İstersen sorunu biraz daha net söyle."

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
