# 📋 Detaylı Malzeme Listesi (BOM - Bill of Materials)

Bu liste, **AI-Friend-Robot** projesinin 4WD (4 Tekerlekli) ve Edge-AI odaklı güncel bileşenlerini içerir.

---

## 🧠 1. Kontrol ve Zeka Katmanı (Beyin)
| Malzeme | Adet | Görev | Notlar |
| :--- | :---: | :--- | :--- |
| **Raspberry Pi 5 (8GB)** | 1 | Ana İşletim Sistemi & AI Yönetimi | Sistemin yüksek seviye beyni. (**Stok bekleniyor**). |
| **Raspberry Pi AI HAT+ (13T)** | 1 | Yapay Zeka Hızlandırıcı | Yüz tanıma ve LLM işlemleri için (**Satın Alındı - 4.299,99 TL**). |
| **Samsung PM981 256GB SSD** | 1 | Yüksek Hızlı Depolama | İşletim sistemi ve modellerin hızlı yüklenmesi için. (**Elimizde var.**) |
| **Ugreen NVMe SSD Kutusu** | 1 | SSD-USB Köprüsü | USB 3.1 üzerinden yüksek hızlı veri transferi. [Ürün Linki](https://www.amazon.com.tr/dp/B07NPFV21H) |
| **STM32F103C8T6 (64K)** | 1 | Hareket ve Sensör Kontrolü | Robotun alt seviye "Omurilik" sistemi (64K Flash versiyonu). [Ürün Linki](https://www.hepsiburada.com/stm32f103c8t6-gelistirme-devre-kart-modulu-p-HBCV0000DKLHL3?magaza=prat%C4%B1ksepet) |
| **ST-Link V2** | 1 | Programlayıcı | STM32'ye kod yüklemek için kullanılır. (Amazon sepetinde). |
| **Raspberry Pi Aktif Soğutucu** | 1 | Termal Yönetim | Pi 5 ve AI modülünü soğutmak için (**Satın Alındı - 472,40 TL**). |

---

## 👁️ 2. Sensörler ve Etkileşim (Duyular)
| Malzeme | Adet | Görev | Notlar |
| :--- | :---: | :--- | :--- |
| **Rpi Camera Module 3** | 1 | Görsel Giriş | Tanem'i tanımak için kullanılır. |
| **USB Mikrofon Dizisi** | 1 | Ses Girişi | Sesli komutları almak için kullanılır. |
| **0.96" I2C OLED Ekran** | 1 | Yüz İfadeleri | Robotun duygusal durumunu gösterir. |
| **HC-SR04** | 2 | Engel Algılama | Güvenli sürüş için mesafe sensörü. |
| **MPU-6050** | 1 | İvmeölçer & Jiroskop | Yön tayini ve stabilizasyon desteği için kullanılır. |

---

## ⚙️ 3. Hareket ve Güç Katmanı (Kaslar)
| Malzeme | Adet | Görev | Notlar |
| :--- | :---: | :--- | :--- |
| **JGB37-520 12V 333RPM** | 4 | Ana Tahrik Motorları | Enkoderli, yüksek torklu metal motorlar. [Ürün Linki](https://www.direnc.net/jgb37-520-12v-330rpm-enkoderli-motor) |
| **37mm Metal Motor Tutucu** | 4 | Motor Montaj Aparatı | [Ürün Linki](https://www.robotzade.com/urun/37-mm-motor-tutucu-aparat-metal) |
| **6mm Kaplin (D-Şaft)** | 4 | Güç Aktarımı | Motor milini tekerleğe bağlar. [Ürün Linki](https://www.direnc.net/6mm-motor-kaplini) |
| **100 mm Kauçuk Tekerlek** | 4 | Hareket (4WD) | Kaplin uyumlu, yüksek arazi kabiliyeti. |
| **30x30 cm Şasi Levhası** | 1 | Ana Taşıyıcı İskelet | Alüminyum veya Kompozit (Özel Kesim). |
| **TB6612FNG Motor Sürücü** | 4 | Motor Güç Yönetimi | Her motor için bağımsız 1 adet sürücü. [Ürün Linki](https://www.direnc.net/tb6612fng-dc-ve-step-motor-surucu-modulu) |
| **Alüminyum Soğutucu Blok** | 4 | Termal Koruma | Sürücü çiplerinin üzerine yapıştırılacak minik plakalar. |
| **18650 Pil (3.7V)** | 4 | Enerji Kaynağı | 4S (14.8V) konfigürasyonunda kullanılacaktır. (**Elimizde 4 adet var.**) |
| **4S 40A Balanslı BMS** | 1 | Pil Güvenliği | Olt - Mor Model. [Ürün Linki](https://www.pilpaketi.com/olt-lityum-iyon-bms-4s-40a-balansli-mor) |
| **16.8V 2A Şarj Adaptörü** | 1 | Güç Girişi | Pilleri güvenli şarj etmek için. [Ürün Linki](https://www.trendyol.com/weko/4s-lityum-batarya-sarj-adaptoru-16-8-volt-2a-p-878198638) |
| **5V 5A Buck Converter** | 1 | Voltaj Regülatörü | 14.8V'u Pi 5 için 5V'a düşürür. |

---

## 🏗️ 4. Bağlantı ve Sarf Malzemeleri
| Malzeme | Adet | Görev | Notlar |
| :--- | :---: | :--- | :--- |
| **Jumper Kablo Seti** | 1 | Bağlantılar | Dişi-Dişi ve Erkek-Dişi karışık paket. |
| **4S 18650 Pil Yuvası** | 1 | Pil Taşıyıcı | Seri bağlantı sağlar. |
| **27W USB-C Adaptör** | 1 | Masaüstü Güç | Pi 5 geliştirme aşamasında kullanılır (Orijinal). |

---

## 📝 Teknik Karar Notları
* **Özel Şasi Tasarımı:** JGB37 motorların yüksek torkunu karşılamak amacıyla 30x30 cm özel levha, metal L-braketler ve **6 mm çelik kaplinler** üzerinden "yüksek şasi" mimarisi kurgulanmıştır.
* **Tekerlek Seçimi:** Engel aşma kabiliyeti ve estetik bütünlük için 100 mm çapında büyük kauçuk tekerlekler tercih edilmiştir.
* **Motor & Sürücü Mimarisi:** Termal kararlılık için her motor için bağımsız 1 adet TB6612FNG sürücü kullanılacaktır.
* **Depolama Stratejisi:** PCIe yolu AI modülüne ayrıldığı için SSD, Ugreen USB 3.1 kutusu ile sisteme dahil edilmiştir.
