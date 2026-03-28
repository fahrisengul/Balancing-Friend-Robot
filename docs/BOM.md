# 📋 Detaylı Malzeme Listesi (BOM - Bill of Materials)

Bu liste, **AI-Friend-Robot** projesinin 4WD (4 Tekerlekli) ve Edge-AI odaklı güncel bileşenlerini içerir.

---

## 🧠 1. Kontrol ve Zeka Katmanı (Beyin)
| Malzeme | Adet | Görev | Notlar |
| :--- | :---: | :--- | :--- |
| **Raspberry Pi 5 (8GB)** | 1 | Ana İşletim Sistemi & AI Yönetimi | Sistemin yüksek seviye beyni. (Stok bekleniyor). |
| **Raspberry Pi AI HAT+ (13T)** | 1 | Yapay Zeka Hızlandırıcı | Yüz tanıma ve LLM işlemleri için (Satın Alındı). |
| **Samsung PM981 256GB SSD** | 1 | Yüksek Hızlı Depolama | İşletim sistemi ve modellerin hızlı yüklenmesi için. |
| **Ugreen NVMe SSD Kutusu** | 1 | SSD-USB Köprüsü | USB 3.1 üzerinden yüksek hızlı veri transferi. |
| **STM32F103C8T6 (64K)** | 1 | Hareket ve Sensör Kontrolü | Robotun alt seviye "Omurilik" sistemi. |
| **ST-Link V2** | 1 | Programlayıcı | STM32'ye kod yüklemek için. |
| **Raspberry Pi Aktif Soğutucu** | 1 | Termal Yönetim | Pi 5 ve AI modülünü soğutmak için (Satın Alındı). |

---

## 👁️ 2. Sensörler ve Etkileşim (Duyular)
| Malzeme | Adet | Görev | Notlar |
| :--- | :---: | :--- | :--- |
| **Rpi Camera Module 3** | 1 | Görsel Giriş | Tanem'i tanımak için kullanılır. |
| **USB Mikrofon Dizisi** | 1 | Ses Girişi | Sesli komutları almak için. |
| **0.96" I2C OLED Ekran** | 1 | Yüz İfadeleri | Robotun duygusal durumunu gösterir. |
| **HC-SR04** | 2 | Engel Algılama | Güvenli sürüş için mesafe sensörü. |
| **MPU-6050** | 1 | İvmeölçer & Jiroskop | Yön tayini ve stabilizasyon desteği için. |

---

## ⚙️ 3. Hareket ve Güç Katmanı (Kaslar)
| Malzeme | Adet | Görev | Notlar |
| :--- | :---: | :--- | :--- |
| **DC Motor (4WD uyumlu)** | 4 | Tahrik Sistemi | 6V-12V arası çalışan standart motorlar. |
| **TB6612FNG** | 1 | Motor Sürücü | STM32 üzerinden çift kanal kontrol. |
| **4WD Şasi Kiti** | 1 | İskelet | Tekerlekler ve montaj platformu dahil. |
| **18650 Pil (3.7V)** | 4 | Enerji Kaynağı | 4S (14.8V) konfigürasyonunda kullanılacak. |
| **4S 18650 Pil Yuvası** | 1 | Pil Taşıyıcı | Seri bağlantı sağlar. |
| **5V 5A Buck Converter** | 1 | Regülatör | 14.8V'u Pi 5 için 5V'a düşürür. |

---

## 🏗️ 4. Bağlantı ve Sarf Malzemeleri
| Malzeme | Adet | Görev | Notlar |
| :--- | :---: | :--- | :--- |
| **Jumper Kablo Seti** | 1 | Bağlantılar | Dişi-Dişi ve Erkek-Dişi karışık paket. |
| **4S BMS Kartı** | 1 | Pil Koruması | Aşırı deşarj ve kısa devre koruması için. |
| **27W USB-C Adaptör** | 1 | Masaüstü Güç | Pi 5 geliştirme aşamasında kullanılır (Orijinal). |

---

## 📝 Teknik Karar Notları
* **Mekanik Değişiklik:** Denge (Balancing) mekanizmasından, stabilite ve AI odaklı çalışma için 4WD (4 Tekerlekli) şasiye geçilmiştir.
* **Hızlandırıcı Seçimi:** Fiyat/Performans dengesi nedeniyle Raspberry Pi AI HAT+ (13 TOPS) tercih edilmiştir.
* **Depolama Stratejisi:** PCIe yolu AI modülüne ayrıldığı için SSD, Ugreen USB 3.1 kutusu ile sisteme dahil edilmiştir.
* **Kontrol Mimarisi:** Motor kontrolü STM32 üzerinde, yapay zeka görevleri Pi 5 üzerinde koşturulmaktadır.
