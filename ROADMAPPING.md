# 🗺️ AI-Friend-Robot Proje Yol Haritası (Roadmap)

Bu belge, robotun teknik gelişimini ve Tanem ile olan etkileşim seviyelerini fazlara ayırarak takip etmemizi sağlar.

---

## 🏁 FAZ 1: "Dijital Doğum" (Elektronik Temel)
**Hedef:** Sistemin elektronik olarak ayağa kaldırılması.
* **Donanım:** Pi 5 + Hailo-8 + 7" QLED Ekran + Camera Module 3.
* **Görevler:** - Raspberry Pi OS ve Hailo-8 sürücülerinin kurulumu.
  - 7" Ekran ve Dokunmatik panel entegrasyonu.
  - Kamera görüntüsünün ekrana aktarılması.
* **Başarı Kriteri:** Ekranın açılması ve temel sistem bileşenlerinin birbirini tanıması.

---

## 🧠 FAZ 2: "Karakterin Ruhu" (Yazılım Derinliği & AI Eğitim)
**Hedef:** Tanem ile etkileşime giren akıllı asistan kimliğinin kazanılması.
* **Gelişmiş AI Etkileşimi:** - **Yüz Tanıma:** Tanem'i gördüğünde ismini söyleyerek karşılama.
  - **LLM (Llama 3 vb.):** Sohbet yeteneği ve "Bellek" (Tanem'in sevdiklerini hatırlama).
  - **Eğitim Modülü:** Günlük ödev ve sorumluluk hatırlatıcı (Soru-cevap şeklinde).
  - **Dil Desteği:** İngilizce pratik yapma seansları.
* **Görevler:** - Speech-to-Text ve Text-to-Speech entegrasyonu.
  - "KUTU" formu yerleşim dizaynı ve prototipleme.
* **Başarı Kriteri:** Robotun masanın üzerinde dururken Tanem ile sesli ve görüntülü iletişim kurması.

---

## 🐕 FAZ 3: "Fiziksel Kimlik" (Poodle Estetiği & Montaj)
**Hedef:** Robotun mekanik montajı ve Poodle formuna kavuşması.
* **Donanım:** 30x30 Şasi + Metal Braketler + Motorlar + 100mm Tekerlekler.
* **Görevler:** - Mekanik şasi montajı.
  - Poodle peluş/plastik dış kabuk uygulaması.
  - 7" Ekranın "Kafa" bölgesine, kameranın "Göz" bölgesine yerleşimi.
* **Başarı Kriteri:** Robotun fiziksel olarak bir "Poodle" gibi görünmesi.

---

## 🚀 FAZ 4: "Otonom Hayat" (Hareket ve Saha Eğitimi)
**Hedef:** Zekanın hareketle birleşmesi ve tam otonom asistanlık.
* **Donanım:** STM32 + 4x Motor Sürücü + 4S Pil Sistemi + Sensörler.
* **Görevler:** - STM32 motor kontrol yazılımı.
  - Engel algılama ve Tanem'i otonom takip algoritmaları.
  - Hareket halindeyken eğitim ve oyun seansları.
* **Başarı Kriteri:** Robotun evin içinde güvenli bir şekilde dolaşarak Tanem'e eşlik etmesi.
