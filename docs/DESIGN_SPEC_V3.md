# ⚙️ Technical Design Spec: Premium Wedge V3

## 📐 1. Geometri ve Form
* **Boyutlar:** 220 x 135 x 105 mm (Genişlik x Derinlik x Arka Yükseklik)
* **Malzeme:** 3D Baskı (PETG/ABS) - 3mm et kalınlığı.

## 🧠 2. İç Yerleşim (Performans Modu)
| Bileşen | Konum | Teknik Detay |
| :--- | :--- | :--- |
| **Pi 5 + AI HAT** | Sol İç Taban | PCIe hattı sadece AI HAT içindir. |
| **4'lü Pil Yuvası** | Arka İç Taban | 80x80x20 mm yerleşim alanı. |
| **SSD (Ugreen)** | Sağ İç Duvar | USB 3.0 portuna bağlı. |
| **Buck Converter** | Orta İç Bölüm | Çıkış: 5.1V - 5.2V arasına set edilecek. |

## 🔌 3. Portlar ve Kontroller
* **Ön Panel:** 8" LCD + Kamera + Mikrofon Dizisi.
* **Sağ Panel:** Ø16mm Power Button.
* **Arka Panel:** 40mm Egzoz Fanı + DC Şarj Girişi (Jack).
