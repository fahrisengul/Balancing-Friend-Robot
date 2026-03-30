# ⚙️ Technical Design Spec: Premium Wedge Terminal V1

## 1. Mekanik Ölçüler
* **Genişlik:** 220 mm | **Derinlik:** 135 mm
* **Yükseklik:** 65 mm (Ön) - 105 mm (Arka)
* **Eğim:** ~60° (Dokunmatik kullanım için optimize)
* **Malzeme:** 3mm PETG / ABS (3D Print)

## 2. Arayüz ve Sensörler
* **Ekran Cutout:** 190mm x 115mm (8" Panel uyumlu)
* **Kamera:** Üst orta konumda Ø12mm dairesel delik.
* **Güç Butonu:** Sağ panelde Ø16mm harici buton (Pi 5 J2 Header bağlantısı).

## 3. Termal & Güç Tasarımı
* **Hava Tüneli:** Sağ panel (Hava girişi) -> Pi 5/Hailo -> 40mm Fan (Arka egzoz).
* **Güç Girişi:** Arka panelde şasiye entegre USB-C soket yuvası.
* **SSD Yerleşimi:** Sağ iç duvar, kablo bükülme toleranslı dikey montaj.

## 4. Montaj Toleransları
* **Genel:** ±0.5 mm
* **Vida Yuvaları:** +0.2 mm
