import pygame
import threading
import random
import time
import json
import os
from face_ui import PoodleFace
from speech_recognition import UnknownValueError
from speech_engine import PoodleSpeech

def load_memory():
    if os.path.exists("memory.json"):
        with open("memory.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {"user_name": "Tanem", "interaction_count": 0}

def save_memory(data):
    with open("memory.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def main():
    pygame.init()
    screen = pygame.display.set_mode((1024, 600))
    clock = pygame.time.Clock()

    face = PoodleFace(1024, 600)
    speech = PoodleSpeech()
    memory = load_memory()
    
    running = True
    is_busy = False
    last_interaction_time = time.time()
    idle_look_timer = 0

    print(f"\n--- Poodle Robot Canlandı (Hafıza: {memory['interaction_count']} etkileşim) ---")

    def voice_interaction():
        nonlocal last_interaction_time, is_busy, memory
        is_busy = True
        
        face.set_state("listening")
        user_text = speech.listen()
        
        if user_text:
            face.set_state("speaking")
            memory["interaction_count"] += 1
            
            # --- GELİŞMİŞ DİYALOG MOTORU ---
            text = user_text.lower()
            
            if "merhaba" in text or "selam" in text:
                responses = [
                    f"Merhaba {memory['user_name']}! Bugün seni gördüğüme çok sevindim.",
                    f"Selam {memory['user_name']}! Yine harika görünüyorsun.",
                    f"Ooo kimleri görüyorum, merhaba {memory['user_name']}!"
                ]
                speech.speak(random.choice(responses))
            
            elif "görüyor" in text:
                speech.speak(f"Evet {memory['user_name']}, seni çok net görebiliyorum. Gözlerin parlıyor!")
            
            elif "duyuyor" in text:
                speech.speak("Seni çok iyi duyuyorum Tanem. Sesin kuş cıvıltısı gibi geliyor.")
                
            elif "nasılsın" in text:
                speech.speak("Harikayım! Seninle vakit geçirmek beni çok mutlu ediyor. Sen nasılsın?")
            
            elif "adın ne" in text or "ismin ne" in text:
                speech.speak("Benim adım Poodle. Senin en sadık robot arkadaşınım.")

            elif "kimsin" in text:
                speech.speak("Ben Fahri'nin senin için tasarladığı akıllı bir robotum. Seninle öğrenmeye bayılıyorum.")
            
            else:
                # Tanımlanamayan cümlelerde papağan modundan kurtulalım
                speech.speak(f"Bunu ilk defa duyuyorum Tanem. '{user_text}' ne demek, bana anlatır mısın?")
            
            save_memory(memory) # Hafızayı güncelle
        
        else:
            face.set_state("error")
            speech.speak("Seni duyamadım Tanem, galiba biraz uzağa gittin.")
        
        face.set_state("idle")
        last_interaction_time = time.time()
        is_busy = False

    while running:
        now = time.time()
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            elif event.type == pygame.KEYDOWN and not is_busy:
                if event.key == pygame.K_l:
                    threading.Thread(target=voice_interaction, daemon=True).start()
                elif event.key == pygame.K_SPACE:
                    face.set_state("speaking")
                    speech.speak(f"Hoş geldin {memory['user_name']}! Seni bekliyordum.")
                elif event.key == pygame.K_q: running = False

        # --- DAVRANIŞ AĞACI (BEHAVIOR) ---
        if not is_busy:
            if now - last_interaction_time > 10:
                if now > idle_look_timer:
                    rx, ry = random.randint(200, 800), random.randint(150, 450)
                    face.update_gaze(rx, ry)
                    idle_look_timer = now + random.uniform(3, 7)
            else:
                face.update_gaze(mouse_pos[0], mouse_pos[1])

        face.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
