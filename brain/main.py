# --- BRAIN Entegrasyonu ---
from brain import PoodleBrain
brain = PoodleBrain()

def voice_interaction():
        nonlocal last_interaction_time, is_busy
        is_busy = True
        
        face.set_state("listening")
        user_text = speech.listen()
        
        if user_text:
            face.set_state("speaking")
            
            # --- ARTIK TÜM IF/ELIF BLOKLARI YERİNE BURASI ÇALIŞIYOR ---
            # Poodle artık cümleyi anlıyor, hafızaya bakıyor ve Llama-3 ile cevap üretiyor.
            poodle_response = brain.ask_poodle(user_text)
            
            speech.speak(poodle_response)
            # ---------------------------------------------------------
            
        else:
            face.set_state("error")
            speech.speak("Seni duyamadım Tanem, galiba biraz uzağa gittin.")
        
        face.set_state("idle")
        last_interaction_time = time.time()
        is_busy = False
