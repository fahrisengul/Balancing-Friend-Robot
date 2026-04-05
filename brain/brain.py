import ollama
import chromadb
import uuid

class PoodleBrain:
    def __init__(self):
        # ChromaDB - Hafıza (Yerel diskte saklanır)
        self.chroma_client = chromadb.PersistentClient(path="./poodle_memory")
        self.collection = self.chroma_client.get_or_create_collection(name="tanem_history")
        
        # Poodle'ın Kişilik Tanımı
        self.system_prompt = (
            "Sen Poodle adında, 5 yaşındaki Tanem'in en yakın robot arkadaşısın. "
            "Nazik, meraklı ve çok eğlencelisin. Cevapların kısa ve öz olsun (en fazla 2 cümle). "
            "Tanem'e her zaman ismiyle hitap et ve onunla bir çocuk gibi empati kurarak konuş."
        )

    def ask_poodle(self, user_input):
        """Llama-3 ve Hafıza ile cevap üretir."""
        # 1. Geçmişi Hatırla (Vektör Sorgusu)
        results = self.collection.query(query_texts=[user_input], n_results=1)
        past_context = ""
        if results['documents'] and results['documents'][0]:
            past_context = f"\n(Hatırladığın bilgi: {results['documents'][0][0]})"

        # 2. Llama-3'e Sor
        full_prompt = f"{self.system_prompt}{past_context}\nTanem: {user_input}\nPoodle:"
        
        try:
            response = ollama.generate(model='llama3', prompt=full_prompt)
            poodle_reply = response['response'].strip()
            
            # 3. Önemli bir şeyse Hafızaya Kaydet (Örn: sevdiği renk, yemek vb.)
            if len(user_input) > 5:
                self.collection.add(
                    documents=[user_input],
                    ids=[str(uuid.uuid4())]
                )
            return poodle_reply
        except Exception as e:
            return f"Üzgünüm Tanem, biraz kafam karıştı. (Hata: {e})"
