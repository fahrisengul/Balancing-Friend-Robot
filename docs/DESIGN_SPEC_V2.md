# ⚙️ Technical Design Spec: Premium Wedge Terminal V2

## 📐 1. Dış Geometri
* **Genişlik:** 220 mm | **Derinlik:** 135 mm
* **Ön Yükseklik:** 65 mm | **Arka Yükseklik:** 105 mm
* **Eğim:** ~60° | **Duvar Kalınlığı:** 3 mm

## 🧠 2. İç Yerleşim ve Montaj Ölçüleri
| Bileşen | Montaj / Delik Ölçüleri | Teknik Not |
| :--- | :--- | :--- |
| **8" Waveshare LCD** | 182.60 x 106.30 mm | 4x M2.5 vida. Cutout: 190.6 x 114.3 mm |
| **Pi 5 + AI HAT** | 58.00 x 49.00 mm | 4x M2.5 standoff (10mm yükseklik) |
| **Powerbank (Slim)** | 145 x 65 x 15 mm | Arka iç tabana kelepçeli/cırtlı montaj |
| **Exhaust Fan (40mm)** | 32.00 x 32.00 mm | Arka panel dairesel ızgara yuvası |
| **Power Button** | Ø 16.20 mm | Sağ yan panel dairesel delik |
| **Camera Module 3** | Ø 12.00 mm | Üst orta odaklı lens deliği |

## 🔌 3. Kritik Port Gereksinimleri
* **Şarj Erişimi:** Powerbank Type-C girişi için arka panelde pencere/yuva.
* **Kablo Payı:** Ugreen SSD ve Pi 5 arasında USB 3.0 kablo bükülme payı için min. 30mm mesafe.
* **Ses:** Yan panellerde 15x15 mm delikli hoparlör ızgaraları.
