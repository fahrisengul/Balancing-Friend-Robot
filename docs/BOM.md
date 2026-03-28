# 📋 Detaylı Malzeme Listesi (BOM - Bill of Materials)

Bu liste, **Balancing-Friend-Robot** projesinin mekanik, elektronik ve yapay zeka katmanlarını kapsayan güncel bileşenleri içerir.

---

## 🧠 1. Kontrol ve Zeka Katmanı (Beyin)
| Malzeme | Adet | Görev | Notlar |
| :--- | :---: | :--- | :--- |
| **Raspberry Pi 5 (8GB)** | 1 | Ana İşletim Sistemi & AI Yönetimi | Robotun "Yüksek Seviye" beyni. |
| **Hailo-8 M.2 AI Kit** | 1 | Yerel Yapay Zeka Hızlandırıcı | Yüz tanıma ve ses-metin işleme için. |
| **STM32F103C8T6 (Bluepill)** | 1 | Hareket ve Denge Kontrolü | Robotun "Alt Seviye" refleks sistemi. |
| **ST-Link V2** | 1 | Programlayıcı | STM32'ye kod yüklemek için. |
| **MicroSD Kart (128GB)** | 1 | Depolama | High Speed (V30) tercih edilmeli. |

---

## 👁️ 2. Sensörler ve Etkileşim (Duyular)
| Malzeme | Adet | Görev | Notlar |
| :--- | :---: | :--- | :--- |
| **MPU-6050** | 1 | İvmeölçer & Jiroskop | Denge için eğim açısını ölçer. |
| **Rpi Camera Module 3** | 1 | Görsel Giriş | Tanem'i tanımak için kullanılır. |
| **USB Mikrofon Dizisi** | 1 | Ses Girişi | Sesli komutları almak için. |
| **0.96" I2C OLED Ekran** | 1 | Yüz İfadeleri | Robotun duygusal durumunu gösterir. |
| **HC-SR04** | 2 | Engel Algılama | Ön ve arka güvenlik için. |
| **DFPlayer Mini + Hoparlör**| 1 | Ses Çıkışı | Müzik ve sesli yanıtlar için. |

---

## ⚙️ 3. Hareket ve Güç Katmanı (Kaslar)
| Malzeme | Adet | Görev | Notlar |
| :--- | :---: | :--- | :--- |
| **12V Encoderlı DC Motor** | 2 | Tahrik Sistemi | Geri bildirimli (Encoder) olmalı. |
| **TB6612FNG** | 1 | Motor Sürücü | STM32 ile kontrol edilir. |
| **80mm Tekerlek Seti** | 1 | Hareket | Silikon/Kauçuk yüzeyli. |
| **11.1V (3S) Li-Po Batarya**| 1 | Ana Güç Kaynağı | ~2200mAh kapasite önerilir. |
| **LM2596 Voltaj Regülatörü**| 2 | Güç Dağıtımı | 5V ve 12V hatları için. |

---

## 🏗️ 4. Mekanik ve Gövde
| Malzeme | Adet | Görev | Notlar |
| :--- | :---: | :--- | :--- |
| **Denge Robotu Şasisi** | 1 | İskelet | 3 Katlı Alüminyum veya Pleksiglas. |
| **Jumper Kablo Seti** | 1 | Bağlantılar | Dişi-Dişi ve Erkek-Dişi karışık. |
| **Güç Anahtarı (Switch)** | 1 | Açma/Kapama | Yüksek akıma dayanıklı. |

---

## 📝 Teknik Karar Notları
* **AI Hızlandırıcı Seçimi:** Başlangıçta Hailo-10 düşünülmüş olsa da, Türkiye pazarındaki ulaşılabilirlik ve fiyat/performans dengesi nedeniyle **Hailo-8 M.2 AI Kit** tercih edilmiştir (Mart 2026).
* **Kontrol Mimarisi:** Denge kararlılığı için motor kontrolü "Bare-Metal" olarak STM32 üzerinde, yapay zeka görevleri ise Raspberry Pi 5 üzerinde koşturulacaktır.
