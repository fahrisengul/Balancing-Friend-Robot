# 🔋 Güç Sistemi Dokümantasyonu (Power System)

Bu döküman, robotun enerji yönetim birimlerini, şarj mimarisini ve güvenlik protokollerini içerir.

## ⚡ Ana Güç Kaynağı
- **Hücre Tipi:** 18650 Li-ion (3.7V Nominal)
- **Konfigürasyon:** 4S1P (4 Seri) - Toplam 14.8V Nominal / 16.8V Peak
- **Kapasite:** 6800 mAh (Etiket Değeri - Test Edilecek)
- **Taşıyıcı:** 4S 18650 Pil Yuvası

## 🛡️ Güç Yönetimi ve Koruma (BMS)
Sistemin güvenli şarj/deşarj olması ve hücreler arası voltaj dengesinin korunması için aşağıdaki modül tercih edilmiştir:

- **BMS Kartı:** [Olt - Lityum İyon Bms - 4s 40a - Balanslı - Mor](https://www.pilpaketi.com/olt-lityum-iyon-bms-4s-40a-balansli-mor?srsltid=AfmBOoqq-RTcucpgOh4NO6t9U_DX8PTd9nffByiE8G_k75QDFWUxsW6d)
- **Özellikler:** - 40A Sürekli akım desteği.
  - Balanslı şarj özelliği (Hücreleri dengeler).
  - Aşırı şarj, aşırı deşarj ve kısa devre koruması.

## 🔌 Şarj Mimarisi
Robotun pilleri, BMS üzerinden güvenli bir şekilde aşağıdaki adaptörle şarj edilecektir:

- **Şarj Adaptörü:** [WEKO 4S Lityum Batarya Şarj Adaptörü 16.8 Volt 2A](https://www.trendyol.com/weko/4s-lityum-batarya-sarj-adaptoru-16-8-volt-2a-p-878198638)
- **Şarj Tipi:** Sabit Akım / Sabit Voltaj (CC/CV)
- **Bağlantı:** Robot gövdesine entegre edilecek bir DC Barrel Jack üzerinden.

## 📉 Voltaj Regülasyonu
Bataryadan gelen ~15V gerilim, alt sistemler için aşağıdaki şekilde dağıtılacaktır:
1. **Yüksek Akım Hattı (15V):** Doğrudan TB6612FNG Motor Sürücüye (Motorlar için).
2. **Kontrol Hattı (5V 5A):** Buck Converter aracılığıyla Raspberry Pi 5 ve Hailo-8 AI Modülüne.

---
*Son Güncelleme: 28 Mart 2026 - Güç bileşenleri kesinleştirildi ve satın alma listesine eklendi.*
