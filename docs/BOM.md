# 💰 Proje Bütçesi ve Maliyet Takibi (AI-Friend-Robot)

Bu dosya, projenin Faz 1 (Terminal) ve Faz 2 (Etkileşim) aşamalarındaki tüm ihtiyaçları kapsar.

## 📊 Genel Özet
* **Toplam Harcanan:** 7.340,83 TL
* **Kalan Bütçe Tahmini:** 19.062 TL + WEKO 4S LİTYUM BATARYA SARJ ADAPTÖRÜ

---

## 🛠️ 1. Satın Alınan / Elimizde Olan Bileşenler
| Tarih | Ürün | Miktar | Birim Fiyat | Toplam | Durum |
| :--- | :--- | :---: | :--- | :--- | :--- |
| 23.03.2026 | Raspberry Pi AI HAT+ (13T) | 1 | 4.299,99 TL | 4.299,99 TL | ✅ Stokta |
| 24.03.2026 | Raspberry Pi Active Cooler | 1 | 472,39 TL | 472,39 TL | ✅ Stokta |
| 01.04.2026 | Özel Kasa Tasarımı & 3D Baskı | 1 | 1.000,00 TL | 1.000,00 TL | ⚙️ Üretimde |
| - | Samsung PM981 256GB SSD | 1 | 0,00 TL | 0,00 TL | ✅ Elimizde Var |
| - | 18650 Pil (4 Adet) + Yuva | 1 | 0,00 TL | 0,00 TL | ✅ Elimizde Var |


- **[x]** 4S 40A Micron BMS (Pilleri korur)  | 150 TL| ✅ sipariş Verildi |
- **[x]** Mini560 5V 5A Buck (Pi 5'i besler) | 220 TL| ✅ sipariş Verildi |
- **[x]** Termal Pad (Soğutma sağlar) | 133 TL| ✅ sipariş Verildi |
- **[x]** DC Jack (5.5x2.1mm) (Eksikse sepetinize ekleyin) | 110 TL| ✅ sipariş Verildi |
- **[x]** Robotistan 10 A SMD Sigorta - 6x2 mm| 150 TL| ✅ sipariş Verildi |
| **Dark USB Type C - M.2 NVMe Disk Kutusu** | SSD-USB Köprüsü | 1 | 799 TL | 🟠 Sepette | 1 |

## | **TOPLAM**  **7.340,83 TL** | 

---

## 🛒 2. Satın Alınacaklar (Faz 1 & Faz 2 Eksiksiz Liste)

| Malzeme | Görev | Miktar | Birim Fiyat | Durum | Faz |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **Raspberry Pi 5 (8GB)** | Ana İşlemci | 1 | 7.000 TL | 🔴 Stok Bekleniyor | 1 |
| **Waveshare 7" DSI LCD (C)** | Kullanıcı Arayüzü | 1 | 3.850 TL | 🟠 Sepette | 1 |
| **RPi Camera Module 3** | Görsel Giriş | 1 | 1.250 TL | 🟠 Sepette | 1 |
| **DIY UPS Seti (BMS+Buck+Jack)** | Güç Yönetimi | 1 | 763 TL | 🟠 Sepette | 1 |
| **Kasa Tasarımı & 3D Baskı** | Gövde | 1 | 1.000 TL | ⚙️ Üretimde | 1 |
| **Stereo Hoparlör & USB Mic** | Ses Etkileşim | 1 | 1.250 TL | 🟠 Sepette | 2 |
| **Montaj Seti (Vida+Kablo)** | Bağlantı Elemanları | 1 | 1.150 TL | 🟢 Planlandı | 1|
| **40mm Fan** |FAN | 1 | 1.000,00 TL | 🟢 Orta | 1 |
| **Ø16mm Güç Butonu** | BUTON | 1 | 1.000,00 TL | 🟢 Orta | 1 |
| **BEKLEYEN TOPLAM** | | | **19.062 TL** | |

## Mevcut "Güç Paketi" Sepetiniz (Final List):
- **[x]** WEKO 4S LİTYUM BATARYA SARJ ADAPTÖRÜ 16.8 VOLT 2A  (Hızlı şarj eder)  | ??? TL|
---

## 📝 Finansal ve Teknik Notlar
* **Kamera:** "Görsel Giriş" için Camera Module 3 bütçeye dahil edilmiştir.
* **Besleme:** Powerbank yerine 5V 5A Buck Converter + 4S Pil sistemiyle AI performansı %100 korunacaktır.
* **Ses:** USB Mikrofon dizisi sayesinde Tanem'in komutları gürültüden arındırılarak alınacaktır.
* **Kritik Uyarı:** Pi 5 8GB fiyatı stok durumuna göre ±%15 değişkenlik gösterebilir.

## Depolama Kararı:
İşletim sistemi ve AI modellerinin hızlı yüklenmesi için MicroSD kart yerine Samsung PM981 256GB NVMe SSD kullanılacaktır. Bağlantı Raspberry Pi 5'in PCIe arayüzü (AI HAT+ üzerinden) ile sağlanacaktır.
Depolama Analizi (28 Mart 2026): Elimizde yüksek hızlı bir Samsung NVMe SSD bulunmasına rağmen, Raspberry Pi 5'in tek PCIe yolunun AI HAT+ (Hailo-8) tarafından kullanılması zorunluluğu nedeniyle, SSD'nin USB 3.0 adaptör üzerinden harici depolama olarak kullanılmasına veya sistemin MicroSD üzerinden koşturulmasına karar verilmiştir.

## 💾 Depolama Çözümü (Kesinleşen)
Cihaz: Samsung PM981 256GB NVMe SSD
Bağlantı: Ugreen USB 3.1 Gen2 Type-C M.2 NVMe Kutusu
Performans: UASP desteği ile USB 3.0 üzerinden yüksek hızlı boot ve veri erişimi.
Strateji: PCIe yolu Hailo AI modülüne ayrılmış, ana işletim sistemi ve LLM modelleri SSD üzerine kurulmuştur.
