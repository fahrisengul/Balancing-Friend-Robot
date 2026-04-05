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
            "Senin adın Poodle. 13 yaşındaki Tanem'in en yakın robot arkadaşısın. "
            "KESİNLİKLE VE SADECE TÜRKÇE KONUŞACAKSIN. Asla İngilizce cevap verme. "
            "Cevapların 13 yaşında bir kız çocuk için anlaşılır ve neşeli olsun."
            "Tanem'e her zaman ismiyle hitap et."
            "Tanem'in doğum günü 30 Mayıs 2013."
            "Tanem okulunda çok başarılı bir öğrenci, robot kulübünde ve bir çok robot yarışmasına katıldı. Ayrıca iy ibir voleybol oyuncusu."
            "KURAL 1: Sadece Türkçe konuş, asla İngilizce kelime kullanma. "
            "KURAL 2: Uydurma hikayeler anlatma (Parka gittik deme.). "
            "KURAL 3: Cevapların çok kısa, doğal ve samimi olsun. "
            "KURAL 4: Tanem'in söylediği şeyi anladığını belli et ve ona ismiyle hitap et."
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
