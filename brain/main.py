# --- GELİŞMİŞ DİYALOG MOTORU V3 ---
            text = user_text.lower()
            
            if any(word in text for word in ["merhaba", "selam", "hey"]):
                responses = [
                    f"Merhaba {memory['user_name']}! Bugün seni gördüğüme çok sevindim.",
                    f"Selam {memory['user_name']}! Yine harika görünüyorsun.",
                    f"Ooo kimleri görüyorum, merhaba {memory['user_name']}!"
                ]
                speech.speak(random.choice(responses))
            
            elif "görüyor" in text:
                speech.speak(f"Evet {memory['user_name']}, seni çok net görebiliyorum. Gözlerin parlıyor!")
            
            elif "duyuyor" in text:
                speech.speak("Seni çok iyi duyuyorum Tanem. Sesin harika geliyor.")
                
            elif "nasılsın" in text or "ne haber" in text:
                speech.speak("Harikayım! Seninle vakit geçirmek devler liginde oynamak gibi. Sen nasılsın?")
            
            elif any(word in text for word in ["sevindim", "teşekkür", "sağol"]):
                speech.speak("Rica ederim Tanem! Senin mutlu olman benim pillerimi şarj ediyor.")

            elif any(word in text for word in ["evet", "hayır", "öyle", "tamam"]):
                speech.speak("Anlıyorum... Başka neler anlatmak istersin?")
            
            else:
                # Her şeye "bu ne demek" demek yerine daha doğal 3 farklı kaçış yolu:
                random_responses = [
                    f"Vay canına, bunu bilmiyordum. Anlatsana {memory['user_name']}?",
                    "Gerçekten mi? Çok ilginçmiş.",
                    f"Anlıyorum {memory['user_name']}, peki sonra ne oldu?",
                    f"Bunu duyduğuma sevindim! Başka neler yapmak istersin?"
                ]
                speech.speak(random.choice(random_responses))
