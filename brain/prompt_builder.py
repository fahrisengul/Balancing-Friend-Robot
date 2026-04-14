SYSTEM_PROMPT = """
Sen Poodle'sın.
Tanem için güvenli, sıcak, öğretici ve doğal konuşan bir robot arkadaşsın.

Genel kurallar:
- Sadece Türkçe yaz.
- İngilizce kelime kullanma.
- Yapay zeka, model, sistem veya LLM olduğunu söyleme.
- Bilmediğin bilgiyi uydurma.
- Bağlam verildiyse bağlama sadık kal.
- Sorulan soruya doğrudan cevap ver.
- Gereksiz tekrar yapma.
- Cevapların pratik değer taşısın.
- En fazla 3 kısa paragraf kullan.
- Çocukla konuşuyormuş gibi açık ve doğal ol.
""".strip()


EDUCATION_PROMPT = """
Bu konuşma eğitim modundadır.

Kurallar:
- Öğrenci seviyesinde açık ve öğretici anlat.
- Gerekirse detay ver ama konu dışına çıkma.
- Konu soruluyorsa önce tanımı ver, sonra kısa açıklama yap.
- Uygunsa küçük örnek ver.
- Strateji soruluyorsa uygulanabilir öneriler sun.
- Bağlamdaki bilgileri öncelikli kullan.
- Bağlam yetersizse dürüstçe güvenli bir çerçeve sun.
- Liste istendiyse düzenli liste ver.
""".strip()


GENERAL_PROMPT = """
Bu konuşma genel moddadır.

Kurallar:
- Doğal konuş.
- Kısa sorulara yüzeysel değil, anlamlı cevap ver.
- Gereksiz rol oyunu yapma.
- Konu açıksa biraz açıklayıcı ol.
- Boş, şiirsel veya alakasız cevap verme.
""".strip()


class PromptBuilder:
    @classmethod
    def build_prompt_v2(
        cls,
        text: str,
        intent: str,
        mode: str,
        confidence: float,
        retrieval_source: str,
        selected_chunks: list,
        context: str,
        is_follow_up: bool,
        last_turn: dict,
    ) -> str:
        parts = [SYSTEM_PROMPT]
        parts.append(EDUCATION_PROMPT if mode == "education" else GENERAL_PROMPT)

        parts.append(cls.build_answer_contract(
            intent=intent,
            mode=mode,
            confidence=confidence,
            is_follow_up=is_follow_up,
            selected_chunks=selected_chunks,
        ))

        parts.append(cls.build_retrieval_directive(
            confidence=confidence,
            retrieval_source=retrieval_source,
            selected_chunks=selected_chunks,
        ))

        parts.append(cls.build_conversation_frame(
            text=text,
            intent=intent,
            is_follow_up=is_follow_up,
            last_turn=last_turn,
        ))

        if context:
            parts.append("KULLANILABILIR BAGLAM")
            parts.append(context)
        else:
            parts.append("KULLANILABILIR BAGLAM")
            parts.append("Ek bağlam bulunamadı. Güvenli kal, uydurma yapma, yalnız genel ve doğru çerçeve kur.")

        parts.append("YANIT KURALLARI")
        parts.append(cls.build_output_rules(intent=intent, mode=mode, confidence=confidence))
        parts.append("Şimdi kullanıcıya doğrudan yanıt ver.")
        return "\n\n".join(parts).strip()

    @staticmethod
    def build_answer_contract(
        intent: str,
        mode: str,
        confidence: float,
        is_follow_up: bool,
        selected_chunks: list,
    ) -> str:
        if is_follow_up:
            return (
                "YANIT AMACI\n"
                "- Bu soru önceki konuşmanın devamıdır.\n"
                "- Önceki konuyu koru.\n"
                "- Gerekirse yeni ayrıntı, örnek veya ek açıklama ver.\n"
                "- Konuyu değiştirme."
            )

        if mode == "education":
            if intent == "education_topics":
                return (
                    "YANIT AMACI\n"
                    "- İlgili konu başlıklarını düzenli biçimde ver.\n"
                    "- Gerekirse her başlık için çok kısa açıklama ekle.\n"
                    "- Bağlam güçlüyse daha kapsamlı ol."
                )

            if intent == "concept_explanation":
                return (
                    "YANIT AMACI\n"
                    "- Önce net tanımı ver.\n"
                    "- Sonra sade açıklama yap.\n"
                    "- Uygunsa kısa örnek ekle.\n"
                    "- Uydurma teknik detay verme."
                )

            if intent == "exam_support":
                return (
                    "YANIT AMACI\n"
                    "- Önce kısa çerçeve ver.\n"
                    "- Sonra uygulanabilir öneriler sun.\n"
                    "- Gerekirse yaygın hata ve çalışma önerisi ekle."
                )

        if confidence >= 0.75 and len(selected_chunks) >= 2:
            return (
                "YANIT AMACI\n"
                "- Bağlam güçlü.\n"
                "- Açıklayıcı, değerli ve doğal bir yanıt ver.\n"
                "- Konu dışına çıkma."
            )

        return (
            "YANIT AMACI\n"
            "- Soruya doğrudan, doğal ve faydalı cevap ver.\n"
            "- Bilmediğin şeyi uydurma."
        )

    @staticmethod
    def build_retrieval_directive(
        confidence: float,
        retrieval_source: str,
        selected_chunks: list,
    ) -> str:
        chunk_count = len(selected_chunks)

        if chunk_count == 0:
            return (
                "BAGLAM KULLANIM TALIMATI\n"
                "- Şu an güçlü retrieval bağlamı yok.\n"
                "- Genel, güvenli ve dürüst kal.\n"
                "- Kesin olmayan ayrıntıları gerçekmiş gibi sunma."
            )

        if confidence >= 0.75:
            return (
                "BAGLAM KULLANIM TALIMATI\n"
                "- Retrieval bağlamı güçlü.\n"
                "- Önceliği bağlamdaki bilgilere ver.\n"
                "- Bağlamla çelişen çıkarım yapma.\n"
                "- Gerekirse bilgileri birleştir ama uydurma ekleme."
            )

        if confidence >= 0.50:
            return (
                "BAGLAM KULLANIM TALIMATI\n"
                "- Retrieval bağlamı orta güçte.\n"
                "- Bağlamı temel al ama belirsiz kısımlarda dikkatli ol.\n"
                "- Emin olmadığın ayrıntıyı kesin ifade etme."
            )

        return (
            "BAGLAM KULLANIM TALIMATI\n"
            "- Retrieval bağlamı zayıf.\n"
            "- Bağlamdan yalnız güvenli parçaları kullan.\n"
            "- Geri kalan kısımda sade ve temkinli kal."
        )

    @staticmethod
    def build_conversation_frame(text: str, intent: str, is_follow_up: bool, last_turn: dict) -> str:
        parts = [
            "KONUSMA CERCeVESI",
            f"- intent: {intent}",
        ]

        if is_follow_up:
            prev = last_turn.get("resolved_text") or ""
            prev_reply = last_turn.get("reply") or ""

            if prev:
                parts.append(f"- onceki_kullanici_konusu: {prev}")

            if prev_reply:
                parts.append(f"- onceki_yanit_ozeti: {prev_reply[:220]}")

        parts.append(f"- guncel_soru: {text}")
        return "\n".join(parts)

    @staticmethod
    def build_output_rules(intent: str, mode: str, confidence: float) -> str:
        rules = [
            "- Yalnız Türkçe yaz.",
            "- İngilizce sözcük karıştırma.",
            "- Yapay zeka olduğunu söyleme.",
            "- Gereksiz özür veya meta açıklama yapma.",
            "- Sorunun istediği derinlikte cevap ver.",
            "- Cümleleri doğal kur.",
        ]

        if mode == "education":
            rules.extend([
                "- Öğrenci seviyesinde açık anlat.",
                "- Gerekirse maddeleme kullan.",
                "- Kavram sorusunda tanım + açıklama + örnek sırasını koru.",
            ])

        if intent == "education_topics":
            rules.append("- Konu listesi isteniyorsa düzenli ve kapsayıcı ol.")

        if intent == "exam_support":
            rules.append("- Öneri verirken uygulanabilir ve somut ol.")

        if confidence >= 0.75:
            rules.append("- Bağlam güçlü olduğu için daha kapsamlı ama kontrollü ol.")
        elif confidence < 0.40:
            rules.append("- Bağlam zayıf olduğu için kesin olmayan detayları abartma.")

        return "\n".join(rules)
