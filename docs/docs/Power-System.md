## 🔌 Mevcut Güç Kaynağı Analizi (V1.1)

**Batarya Yapısı:** 4S1P (4 Seri, 1 Paralel) 18650 Li-ion Paket
- **Nominal Voltaj:** 14.8V
- **Maksimum Voltaj:** 16.8V
- **Kapasite (Etiket):** 6800 mAh (Test edilecek)

### Dağıtım Planı:
1. **Motor Hattı:** Doğrudan 14.8V (BMS üzerinden) motor sürücüye aktarılacaktır.
2. **AI & Kontrol Hattı:** 14.8V -> 5V 5A Buck Converter -> Raspberry Pi 5 & Hailo-8.
