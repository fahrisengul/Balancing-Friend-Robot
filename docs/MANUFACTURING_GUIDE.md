# 🛠️ Üretim ve 3D Baskı Kılavuzu (V2 - AI Eğitim Terminali)

Bu doküman, "Premium Wedge" kasanın 3D tasarım, prototipleme ve üretim standartlarını içerir. Bu proje bir hobi kutusu değil, son kullanıcıya sunulacak bir ürünün ilk prototipidir.

## 🎯 Üretim Hedefi
- **Estetik:** Çocuk dostu, modern ve "Premium" teknolojik görünüm.
- **Sağlamlık:** Günlük masaüstü kullanımına uygun rijit ve dengeli yapı.
- **Mühendislik Doğruluğu:** Isı tahliyesi (Hava tüneli) ve dahili güç kaynağı entegrasyonu.

## 📐 Dış Geometri ve Form
| Parametre | Değer |
| :--- | :--- |
| **Form** | Eğimli Masaüstü (Wedge) |
| **Genişlik / Derinlik** | 220 mm / 135 mm |
| **Ön / Arka Yükseklik** | 65 mm / 105 mm |
| **Açı / Et Kalınlığı** | ~60° / 3 mm |

## 📺 Ekran ve Kamera Entegrasyonu
- **8” Waveshare HDMI LCD (H):** 190.6mm x 114.3mm panel yuvası. 
- **Montaj:** Arka taraftan 182.60 x 106.30 mm eksenli 4x M2.5 vida deliği.
- **Kamera:** Üst orta konumda Ø12mm dairesel lens deliği ve 12x4mm flex kablo geçiş kanalı.

## 🧠 İç Yerleşim ve Donanım
- **Ana Kart:** Raspberry Pi 5 + AI HAT (Sol iç taban). 58x49 mm montaj gridi, 10mm standoff.
- **Mobil Güç:** Baseus Adaman Slim Powerbank (145x65x15 mm). Arka iç tabana sabitlenmiş yuva/kelepçe sistemi.
- **SSD (Ugreen):** Sağ iç duvar. USB 3.0 kablo bükülme payı (min. 30mm) korunarak dikey montaj.
- **Ses:** Yan panellerde 15x15 mm ölçülerinde hoparlör ızgara delikleri.

## 🌡️ Termal Tasarım (Kritik)
- **Aktif Tahliye:** Arka panelde 40x40mm egzoz fanı (32mm delik aralığı, Ø38mm hava deliği).
- **Pasif Giriş:** Sağ panelde 5-6 adet 20x3mm vent slotu.
- **Akış Hattı:** Sağ (Giriş) → Pi 5 + AI HAT → Aktif Soğutucu → Arka Fan → Çıkış.

## 🔌 Portlar ve Kontroller
- **Güç Butonu:** Sağ yan panelde Ø16.2mm dairesel montaj deliği.
- **Şarj Erişimi:** Dahili powerbank'in şarj girişi için arka panelde USB-C erişim penceresi.
- **Arka Panel:** USB-C (Sistem besleme), opsiyonel USB-A ve Ethernet çıkışları için uygun kesikler.

## 🖨️ 3D Baskı Gereksinimleri
- **Malzeme:** PETG veya ABS (Isı dayanımı ve rijitlik için).
- **Katman / Nozzle:** 0.2 mm / 0.4 mm.
- **Dolgu / Duvar:** %25-30 Infill / 4 Perimeter (Vida yuvası dayanımı için).

## ⚙️ Toleranslar
- **Genel:** ±0.5 mm
- **Vida Delikleri:** +0.2 mm
- **Geçme ve Slotlar:** +0.3 mm
---


# 🛠️ Manufacturing Guide (DIY Power Update)

## 🏗️ Yapısal Gereksinimler
- **Alt Kapak:** Batarya değişimi ve BMS kontrolü için kolay sökülebilir (M3 vida) olmalıdır.
- **İzolasyon:** 18650 pil grubu ve BMS kartı kasa içinde kısa devreye karşı yalıtılmalıdır.

## 🌡️ Termal Yönetim
- **Hava Akışı:** Sağ panel giriş slotları -> Pi 5/AI HAT -> 40mm Arka Egzoz Fanı.
- **Isı Kaynakları:** Buck Converter ve BMS kartı, fanın hava akış hattı üzerinde konumlandırılmalıdır.

## ⚡ Montaj Uyarısı
- Şarj girişi (DC Jack) doğrudan BMS "P+" ve "P-" uçlarına bağlanmalıdır.
- Pi 5 beslemesi Buck Converter üzerinden geçmeli, voltaj 5.1V üzerine çıkmamalıdır.

**Not:** Tasarımcıdan STL ve düzenlenebilir STEP formatlarında teslimat beklenmektedir. Kasa içi kablo yönetim kanalları eklenmeli ve batarya ağırlık merkezinin cihazın stabilitesini artıracak şekilde konumlandırılması sağlanmalıdır.
