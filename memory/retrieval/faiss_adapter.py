class FaissAdapter:
    def __init__(self):
        # mevcut init’ini kullan
        pass

    def search(self, query: str, top_k: int = 5):
        # mevcut FAISS search çağrını buraya bağla
        # örnek dönüş:
        # [{"id": "...", "content": "...", "score": 0.82}, ...]
        return []

    def add_short_term(self, items: list[dict]):
        # mevcut short-term ekleme mantığın
        pass
