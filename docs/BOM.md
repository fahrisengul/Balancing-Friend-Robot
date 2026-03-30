# 📋 Detaylı Malzeme Listesi (BOM - Bill of Materials)

Bu liste, **AI-Friend-Robot** projesinin 4WD (4 Tekerlekli) ve Edge-AI odaklı güncel bileşenlerini içerir.

| Malzeme | Adet | Görev | Faz | Durum |
| :--- | :---: | :--- | :---: | :--- |
| **Raspberry Pi 5 (8GB)** | 1 | Ana İşlemci | 1 | Araştırılıyor |
| **Raspberry Pi AI HAT+ (13T)** | 1 | AI Hızlandırıcı | 1 | **Satın Alındı (Geldi)** |
| **8" Capacitive Touch LCD** | 1 | Kullanıcı Arayüzü | 1 | Sepette (Salı) |
| **Raspberry Pi Camera Module 3** | 1 | Görsel Giriş | 1 | Sepette (Salı) |
| **Samsung PM981 256GB SSD** | 1 | Depolama | 1 | **Elimizde Var** |
| **Ugreen NVMe Enclosure** | 1 | SSD-USB Köprüsü | 1 | Sepette (Salı) |
| **Raspberry Pi Active Cooler** | 1 | İşlemci Soğutma | 1 | **Satın Alındı (Bekleniyor)** |
| **40x40mm Exhaust Fan** | 1 | Kasa Havalandırma | 1 | Sepette (Salı) |
| **Ø16mm Power Button** | 1 | Harici Güç Kontrolü | 1 | Sepette (Salı) |
| **USB Mikrofon Dizisi** | 1 | Ses Girişi | 2 | Sepette (Salı) |
| **Stereo Hoparlör Seti** | 1 | Ses Çıkışı | 2 | Sepette (Salı) |
| **JGB37-520 12V Motor** | 4 | Tahrik Sistemi | 3 | Sepette (Salı) |
| **100mm Kauçuk Tekerlek** | 4 | Hareket | 3 | Sepette (Salı) |
| **STM32F103C8T6** | 1 | Alt Seviye Kontrol | 4 | Sepette (Salı) |
| **5V 5A Buck Converter** | 1 | Voltaj Regülasyonu | 4 | Sepette (Salı) |

---

## 🧠 1. Kontrol ve Zeka Katmanı (Beyin)
| Malzeme | Adet | Görev | Notlar |
| :--- | :---: | :--- | :--- |
| **Raspberry Pi 5 (8GB)** | 1 | Ana İşletim Sistemi | Sistemin yüksek seviye beyni. (Stok bekleniyor). |
| **Raspberry Pi AI HAT+ (13T)** | 1 | AI Hızlandırıcı | Hailo-8 tabanlı AI modülü. (**Satın Alındı**). |
| **Samsung PM981 256GB SSD** | 1 | Yüksek Hızlı Depolama | OS ve Modellerin hızlı yüklenmesi için. (**Elimizde var**) |
| **Ugreen NVMe SSD Kutusu** | 1 | SSD-USB Köprüsü | USB 3.1 üzerinden yüksek hızlı veri transferi. |
| **Raspberry Pi Aktif Soğutucu** | 1 | Termal Yönetim | Pi 5 ve AI modülünü doğrudan soğutmak için. (**Satın Alındı**) |
| **STM32F103C8T6 (64K)** | 1 | Hareket Kontrolü | Robotun alt seviye "Omurilik" sistemi. |
| **ST-Link V2** | 1 | Programlayıcı | STM32'ye kod yüklemek için kullanılır. |

---

## 👁️ 2. Arayüz, Sensörler ve Terminal (Duyular & Yüz)
| Malzeme | Adet | Görev | Notlar |
| :--- | :---: | :--- | :--- |
| **8" Capacitive Touch LCD** | 1 | Robotun Yüzü & Arayüz | Premium Wedge kasaya uygun büyük format panel. |
| **Rpi Camera Module 3** | 1 | Görsel Giriş | Tanem'i tanımak için (Ø12mm yuvaya monte edilecek). |
| **USB Mikrofon Dizisi** | 1 | Ses Girişi | Sesli komutlar ve İngilizce eğitimi için. |
| **Stereo Hoparlör Seti** | 1 | Ses Çıkışı | Robotun konuşması ve sesli yanıtları için. |
| **40x40mm Exhaust Fan** | 1 | Kasa Tahliye Fanı | Kasa içi hava tüneli çıkış fanı (Arka Panel). |
| **Ø16mm Power Button** | 1 | Güç Düğmesi | Işıklı, bas-bırak buton (Kasa yan panel). |
| **HC-SR04** | 2 | Engel Algılama | Güvenli otonom sürüş için mesafe sensörü. |
| **MPU-6050** | 1 | Stabilizasyon | İvmeölçer & Jiroskop (Yön tayini için). |

---

## ⚙️ 3. Hareket ve Güç Katmanı (Kaslar)
| Malzeme | Adet | Görev | Notlar |
| :--- | :---: | :--- | :--- |
| **JGB37-520 12V 333RPM** | 4 | Ana Tahrik Motorları | Enkoderli, yüksek torklu metal motorlar. |
| **37mm Metal Motor Tutucu** | 4 | Motor Montajı | Şasiye sabitleme için L-braketler. |
| **6mm Kaplin (D-Şaft)** | 4 | Güç Aktarımı | Motor milini 100mm tekerleğe bağlar. |
| **100 mm Kauçuk Tekerlek** | 4 | Hareket (4WD) | Yüksek tutunuşlu, büyük çaplı tekerlekler. |
| **TB6612FNG Motor Sürücü** | 4 | Güç Yönetimi | Her motor için bağımsız kanal. |
| **18650 Pil (3.7V)** | 4 | Enerji Kaynağı | 4S (14.8V) konfigürasyonu. (**Elimizde 4 adet var**) |
| **4S 40A Balanslı BMS** | 1 | Pil Güvenliği | Hücre dengeleme ve güvenli deşarj. |
| **5V 5A Buck Converter** | 1 | Voltaj Regülatörü | 14.8V'u Pi 5 ve 8" ekran için 5V'a düşürür. |
| **16.8V 2A Şarj Adaptörü** | 1 | Şarj Girişi | Pilleri güvenli şarj etmek için. |

---

## 🏗️ 4. Şasi ve Sarf Malzemeleri
| Malzeme | Adet | Görev | Notlar |
| :--- | :---: | :--- | :--- |
| **Premium Wedge Kasa** | 1 | Masaüstü Terminal | 3D Baskı (PETG) veya Özel Üretim gövde. |
| **30x30 cm Şasi Levhası** | 1 | Ana Taşıyıcı | Robotun yürüyen iskeleti (Metal/Kompozit). |
| **Jumper Kablo Seti** | 1 | Bağlantılar | Dişi-Dişi ve Erkek-Dişi karışık paket. |
| **27W USB-C Adaptör** | 1 | Masaüstü Güç | Geliştirme aşamasında (Faz 1-2) doğrudan besleme. |

---

## 📝 Teknik Karar Notları
* **Kasa Tasarımı:** "Premium Wedge" formu, 8 inçlik ekran için optimize edilmiş olup, sağdan sola hava tüneli ve arka egzoz fanı ile termal yönetim sağlar.
* **Terminal Konforu:** Kullanıcı deneyimini artırmak için Ø16mm harici güç butonu ve arkada sabit adaptör girişi tasarlanmıştır.
* **Ses ve Görüntü:** 8" ekran ve stereo hoparlörlerle robotun "Eğitim Koçu" kimliği güçlendirilmiştir.
* **Güç Stratejisi:** Yüksek akım çeken Pi 5 ve 8" ekranın aynı anda beslenmesi için 5 Amperlik regülatör zorunlu tutulmuştur.
