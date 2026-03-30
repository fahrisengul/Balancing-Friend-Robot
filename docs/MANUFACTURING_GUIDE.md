# 🛠️ Üretim ve 3D Baskı Kılavuzu (V1 - AI Eğitim Terminali)

Bu doküman, "Premium Wedge" kasanın 3D tasarım, prototipleme ve üretim standartlarını içerir. Bu proje bir hobi kutusu değil, son kullanıcıya sunulacak bir ürünün ilk prototipidir.

## 🎯 Üretim Hedefi
- **Estetik:** Çocuk dostu, modern ve şık görünüm.
- **Sağlamlık:** Günlük masaüstü kullanımına uygun rijit yapı.
- **Mühendislik Doğruluğu:** Isı tahliyesi ve kablo gerilimi hesaplanmış iç hacim.

## 📐 Dış Geometri ve Form
| Parametre | Değer |
| :--- | :--- |
| **Form** | Eğimli Masaüstü (Wedge) |
| **Genişlik / Derinlik** | 220 mm / 135 mm |
| **Ön / Arka Yükseklik** | 65 mm / 105 mm |
| **Açı / Et Kalınlığı** | ~60° / 3 mm |

## 📺 Ekran ve Kamera Entegrasyonu
- **8” Kapasitif Ekran:** 190mm x 115mm cutout. Arka taraftan M3 vida veya bracket ile sabitleme.
- **Kamera:** Üst orta konumda Ø12mm dairesel delik ve 12x4mm flex kablo slotu.

## 🧠 İç Yerleşim ve Donanım
- **Ana Kart:** Raspberry Pi 5 + AI HAT (Sol iç taban).
- **Standoff:** 10 mm yükseklik, M2.5 vida uyumlu.
- **SSD (Ugreen):** Sağ iç duvar, kablo bükülme payı bırakılmış dikey/yarı açık slot.

## 🌡️ Termal Tasarım (Kritik)
- **Aktif Tahliye:** Arka panelde 40x40mm egzoz fanı (32mm delik aralığı).
- **Pasif Giriş:** Sağ panelde 5-6 adet 20x3mm vent slotu.
- **Akış Hattı:** Sağ (Giriş) → Pi 5/AI HAT → Fan → Arka (Çıkış).

## 🔌 Portlar ve Kontroller
- **Arka Panel:** USB-C (Power: 12x7mm), Opsiyonel 2x USB-A ve Ethernet yuvaları.
- **Güç Butonu:** Sağ panelde Ø16mm buton deliği.

## 🖨️ 3D Baskı Gereksinimleri
- **Malzeme:** PETG veya ABS (Isı dayanımı için).
- **Katman / Nozzle:** 0.2 mm / 0.4 mm.
- **Dolgu / Duvar:** %20-30 Infill / 3-4 Perimeter.

## ⚙️ Toleranslar
- **Genel:** ±0.5 mm
- **Vida Delikleri:** +0.2 mm
- **Slotlar/Geçmeler:** +0.3 mm

---
**Not:** Tasarımcıdan STL ve STEP formatlarında teslimat beklenmektedir. İçeride kablo sıkışması olmaması ve AI HAT yüksekliği (min. 50mm üst boşluk) hayati önem taşır.
