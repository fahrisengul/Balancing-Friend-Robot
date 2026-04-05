import os
import wave
import array
import subprocess
import speech_recognition as sr
from piper.voice import PiperVoice


class PoodleSpeech:
    def __init__(self, lang="tr-TR"):
        self.recognizer = sr.Recognizer()
        self.lang = lang
        self.voice = None
        self.microphone = None

        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_path = os.path.join(current_dir, "tr_TR-fahrettin-medium.onnx")

        try:
            print(">>> Piper modeli belleğe yükleniyor (Lütfen bekleyin)...")

            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Model bulunamadı: {self.model_path}")

            self.voice = PiperVoice.load(self.model_path)

            import pyaudio
            self.microphone = sr.Microphone()

            print(">>> [SES] Poodle kulağını açtı, ses motoru sıcak ve hazır!")

        except Exception as e:
            print(f">>> [HATA] Başlatma hatası: {e}")

    def _chunk_to_bytes(self, chunk):
        """
        Piper'ın döndürdüğü AudioChunk nesnesini ham PCM bytes'a çevirir.
        Farklı Piper sürümlerine karşı toleranslı yazılmıştır.
        """
        # 1) chunk doğrudan bytes ise
        if isinstance(chunk, (bytes, bytearray)):
            return bytes(chunk)

        # 2) Yaygın olası alanlar
        candidate_attrs = [
            "audio_int16_bytes",
            "audio_bytes",
            "pcm_bytes",
            "buffer",
            "audio",
            "samples",
        ]

        for attr in candidate_attrs:
            if hasattr(chunk, attr):
                value = getattr(chunk, attr)

                if value is None:
                    continue

                if isinstance(value, (bytes, bytearray)):
                    return bytes(value)

                # list / tuple / array benzeri int16 örnekleri
                if isinstance(value, (list, tuple, array.array)):
                    arr = array.array("h", value)
                    return arr.tobytes()

                # numpy benzeri obje ise
                if hasattr(value, "dtype") and hasattr(value, "tobytes"):
                    return value.astype("int16").tobytes()

        # 3) Chunk iterable ise sayı dizisi olabilir
        try:
            seq = list(chunk)
            if seq and isinstance(seq[0], int):
                arr = array.array("h", seq)
                return arr.tobytes()
        except Exception:
            pass

        raise RuntimeError(
            f"AudioChunk çözümlenemedi. type={type(chunk)}, attrs={dir(chunk)}"
        )

    def speak(self, text):
        if not text:
            return

        if not self.voice:
            print(">>> [SES HATASI] Piper voice yüklenemedi.")
            return

        print(f"Poodle: {text}")

        filename = os.path.abspath("poodle_voice.wav")

        try:
            if os.path.exists(filename):
                os.remove(filename)

            sample_rate = self.voice.config.sample_rate
            pcm_buffer = bytearray()

            print(">>> [DEBUG] synthesize() ile ses chunk'ları alınıyor...")

            chunk_count = 0
            for chunk in self.voice.synthesize(text):
                chunk_bytes = self._chunk_to_bytes(chunk)
                if chunk_bytes:
                    pcm_buffer.extend(chunk_bytes)
                    chunk_count += 1

            print(f">>> [DEBUG] chunk_count={chunk_count}")
            print(f">>> [DEBUG] pcm_size={len(pcm_buffer)} byte")

            if len(pcm_buffer) == 0:
                raise RuntimeError("Piper ses verisi üretmedi. PCM buffer boş.")

            with wave.open(filename, "wb") as wav_file:
                wav_file.setnchannels(1)      # mono
                wav_file.setsampwidth(2)      # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(bytes(pcm_buffer))

            if not os.path.exists(filename):
                raise RuntimeError("WAV dosyası oluşmadı.")

            wav_size = os.path.getsize(filename)
            print(f">>> [DEBUG] WAV SIZE={wav_size} byte")

            if wav_size == 0:
                raise RuntimeError("WAV dosyası boş oluştu.")

            result = subprocess.run(
                ["/usr/bin/afplay", filename],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True
            )

            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or "afplay başarısız oldu.")

        except Exception as e:
            print(f">>> [SES HATASI] {type(e).__name__}: {e}")

        finally:
            # Test süresince bırakmak istersen bunu yorum satırı yap
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                except Exception:
                    pass

    def listen(self):
        if not self.microphone:
            return None

        with self.microphone as source:
            print("\n[Dinleniyor...] Poodle seni duymaya hazır...")
            try:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                audio = self.recognizer.listen(source, timeout=4, phrase_time_limit=6)
                text = self.recognizer.recognize_google(audio, language=self.lang)
                print(f"Tanem: {text}")
                return text.lower()

            except sr.WaitTimeoutError:
                return None
            except sr.UnknownValueError:
                return None
            except sr.RequestError as e:
                print(f">>> [DINLEME HATASI] Google STT erişim hatası: {e}")
                return None
            except Exception as e:
                print(f">>> [DINLEME HATASI] {e}")
                return None
