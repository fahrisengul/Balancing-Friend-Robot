import chromadb
import uuid

class PoodleMemory:
    def __init__(self, db_path="./chroma_db"):
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(name="poodle_memory")

    def save_interaction(self, user_text, robot_response):
        """Konuşmayı hafızaya kaydeder."""
        text_to_save = f"Tanem: {user_text} | Poodle: {robot_response}"
        self.collection.add(
            documents=[text_to_save],
            ids=[str(uuid.uuid4())]
        )

    def get_context(self, query, n_results=3):
        """En alakalı son 3 anıyı getirir."""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return " ".join(results['documents'][0]) if results['documents'] else ""
