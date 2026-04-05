import chromadb
import uuid

class PoodleMemory:
    def __init__(self, path="./poodle_memory"):
        self.chroma_client = chromadb.PersistentClient(path=path)
        self.collection = self.chroma_client.get_or_create_collection(name="tanem_history")

    def query_past(self, user_input):
        """Geçmişi hatırlar."""
        results = self.collection.query(query_texts=[user_input], n_results=3)
        if results['documents'] and results['documents'][0]:
            return f"\n(Hatırladığın bilgi: {results['documents'][0][0]})"
        return ""

    def save_to_memory(self, user_input):
        """Önemli bilgileri kaydeder."""
        if len(user_input) > 5:
            self.collection.add(
                documents=[user_input],
                ids=[str(uuid.uuid4())]
            )
