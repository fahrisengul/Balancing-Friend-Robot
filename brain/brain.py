# SADELEŞTİRİLMİŞ, kritik kısımlar

def handle(self, text, session_id=None):
    text = (text or "").strip()

    intent = self.detect_intent(text)
    mode = self._detect_mode(text, intent)

    # 🔹 FAST TRACK (sadece deterministic)
    fast = self._try_fast_track(text, intent, mode)
    if fast:
        return self._log_and_return(
            text=text,
            intent=intent,
            source="fast_track",
            reply=fast,
            session_id=session_id,
        )

    # 🔹 RAG
    bundle = self.retriever.get_context_bundle(
        text=text,
        intent=intent,
        mode=mode,
        top_k=4,
    )

    context = bundle["context_text"]
    confidence = bundle["confidence"]

    # 🔥 MODE SELECTION (KRİTİK)
    llm_mode = self._select_llm_mode(intent, mode, confidence)

    prompt = self._build_prompt(
        text=text,
        intent=intent,
        mode=mode,
        context=context,
        confidence=confidence,
    )

    raw = self.llm.generate(prompt, mode=llm_mode)
    reply = self.policy.apply(raw)

    return self._log_and_return(
        text=text,
        intent=intent,
        source="llm",
        reply=reply,
        session_id=session_id,
    )
