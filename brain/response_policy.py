class ResponsePolicy:

    def apply(self, text: str) -> str:
        if not text:
            return "Bunu tam anlayamadım, tekrar söyler misin?"

        # çok uzun kes
        sentences = text.split(".")
        return ".".join(sentences[:2]).strip()
