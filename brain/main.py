def voice_interaction():
        nonlocal last_interaction_time, is_busy
        is_busy = True
        
        face.set_state("listening")
        user_text = speech.listen()
        
        if user_text:
            face.set_state("speaking")
            
            # --- DIYALOG MOTORU (BASIT LLM MANTIGI) ---
            if "merhaba" in user_text or "selam" in user_text:
                speech.speak("Merhaba Tanem! Bugün seninle yeni şeyler öğrenmek için çok heyecanlıyım.")
            
            elif "görüyor" in user_text or "görüyor musun" in user_text:
                speech.speak("Evet Tanem, seni çok net görebiliyorum. Gözlerin parlıyor!")
            
            elif "duyuyor" in user_text or "duyuyor musun" in user_text:
                speech.speak("Seni çok iyi duyuyorum. Sesin harika geliyor.")
                
            elif "nasılsın" in user_text:
                speech.speak("Harikayım! Seninle vakit geçirmek beni çok mutlu ediyor. Sen nasılsın?")
            
            else:
                # Tanımsız bir şey söylerse meraklı bir cevap versin
                speech.speak(f"Bunu ilk defa duyuyorum. '{user_text}' ne demek Tanem?")
        
        else:
            face.set_state("error")
            speech.speak("Üzgünüm Tanem, seni duyamadım. Tekrar söyler misin?")
        
        face.set_state("idle")
        last_interaction_time = time.time()
        is_busy = False
