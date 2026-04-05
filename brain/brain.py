import ollama
from .memory_manager import PoodleMemory  # Nokta işareti klasör içini temsil eder
from .config import SYSTEM_PROMPT, OLLAMA_MODEL

class PoodleBrain:
    def __init__(self):
        self.memory = PoodleMemory()
        self.system_prompt = SYSTEM_PROMPT

    def ask_poodle(self, user_input):
        """Llama-3 ve Hafıza ile cevap üretir."""
        # 1. Hafızadan bilgi çek
        past_context = self.memory.query_past(user_input)

        # 2. Llama-3'e Sor
        full_prompt = f"{self.system_prompt}{past_context}\nTanem: {user_input}\nPoodle:"
        
        try:
            response = ollama.generate(model=OLLAMA_MODEL, prompt=full_prompt)
            poodle_reply = response['response'].strip()
            
            # 3. Hafızaya Kaydet
            self.memory.save_to_memory(user_input)
            
            return poodle_reply
        except Exception as e:
            return f"Üzgünüm Tanem, biraz kafam karıştı. (Hata: {e})"
