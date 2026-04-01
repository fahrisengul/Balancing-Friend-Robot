# ⚙️ Premium Wedge AI-Friend-Robot: Teknik Tasarım Spesifikasyonları (Master V4)

Bu doküman; robotun dış gövde (kasa), iç yerleşim ve teknik port çıkışlarının nihai tasarım standartlarını belirler. Önceki tüm versiyonların yerini alan güncel rehberdir.

---

## 📐 1. Geometri ve Form Faktörü (Wedge)
* **Tasarım Dili:** Masaüstü Terminal / Eğik Panel (Wedge)
* **Genişlik:** 220 mm
* **Derinlik:** 135 mm
* **Ön Yükseklik:** 65 mm
* **Arka Yükseklik:** 105 mm
* **Eğim Açısı:** ~60° (Göz hizası ergonomisi için)
* **Et Kalınlığı:** 3 mm (PETG/ABS 3D Baskı için optimize edilmiştir)

---

## 🧠 2. İç Yerleşim Planı (Performance Stack)

| Bileşen | Konum | Montaj Detayı |
| :--- | :--- | :--- |
| **7" DSI LCD (C)** | Ön Panel (Merkez) | 165x100mm cutout. Ekran arkasındaki M2.5 yuvalara sabitlenir. |
| **Pi 5 + AI HAT** | Ekran Arkası | Ekranın arkasına "Sandviç" şeklinde monte edilir (DSI kablosu ile). |
| **4'lü Pil Yuvası** | Arka İç Taban | 80 x 80 x 20 mm alan. Isı yalıtımlı bölme. |
| **BMS & Buck Conv.** | Pil Yuvası Yanı | Buck Converter 5.1V - 5.2V arasına set edilmiştir. |
| **Ugreen NVMe SSD** | Sağ İç Duvar | Pi 5 ile arasında 30mm kablo bükülme payı bırakılmalıdır. |
| **Stereo Hoparlörler** | Sol ve Sağ Yanlar | 20x20mm ses ızgaralarının hemen arkasına. |

---

## 🔌 3. Dış Panel Port Haritası (I/O)

| Port / Bileşen | Panel Konumu | Ölçü | Görev |
| :--- | :--- | :--- | :--- |
| **DC Şarj Girişi** | Arka Panel | Ø 8.0 mm | 16.8V Şarj adaptörü girişi. |
| **Ana Güç Butonu** | Sağ Yan Panel | Ø 16.2 mm | Işıklı Metal Power Button. |
| **Egzoz Fanı** | Arka Panel | Ø 38-40 mm | 40mm tahliye fanı (ızgaralı). |
| **Kamera Lensi** | Ön Panel (Üst) | Ø 12.0 mm | RPi Camera Module 3. |
| **Hava Girişleri** | Sağ Panel | 15x60 mm | Soğuk hava giriş slotları. |
| **Ses Izgaraları** | Yan Paneller | 20x20 mm | Stereo ses çıkışı (Delikli doku). |

---

## 🌡️ 4. Termal Yönetim ve Akustik
* **Hava Tüneli:** Sağ paneldeki giriş slotlarından giren hava, Pi 5/AI HAT ikilisini soğutarak arka paneldeki 40mm fan üzerinden tahliye edilir.
* **Isı Yalıtımı:** Batarya grubu (4x18650) ve BMS kartı, işlemci ısısından etkilenmemesi için kasanın alt/arka kısmında izole edilmiştir.
* **Mikrofon İzolasyonu:** USB mikrofon dizisi, fan titreşiminden etkilenmemesi için yumuşak conta/sünger yatak ile monte edilecektir.

---

## ⚡ 5. Güç Stratejisi (DIY UPS)
* **Yapı:** 4S Li-ion (14.8V nominal) -> 5V 5A Buck Converter -> Pi 5 & Ekran.
* **Şarj:** Cihaz çalışırken şarj edilebilir (Pass-through charging) yapıdadır.
* **Kablo Yönetimi:** Ekran HDMI yerine **DSI (yassı kablo)** ile bağlandığı için kasa içinde kablo karmaşası minimize edilmiştir.

---

### 📝 Tasarımcı İçin Önemli Notlar:
1. Önceki versiyonlardaki 8 inç ekran ve HDMI kablo yerleşimi iptal edilmiştir.
2. Güncel tasarım **7 inç DSI (C)** ekran ve **DIY Pil Paketi** üzerine kurgulanmıştır.
3. Kasa içindeki tüm bileşenlerin (özellikle SSD kutusu ve pil yuvası) sarsılmaması için sabitleyici tırnaklar/kanallar eklenmelidir.
