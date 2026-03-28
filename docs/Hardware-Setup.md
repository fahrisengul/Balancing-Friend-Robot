### Depolama Kararı:
- İşletim sistemi ve AI modellerinin hızlı yüklenmesi için MicroSD kart yerine Samsung PM981 256GB NVMe SSD kullanılacaktır. Bağlantı Raspberry Pi 5'in PCIe arayüzü (AI HAT+ üzerinden) ile sağlanacaktır.
- **Depolama Analizi (28 Mart 2026):** Elimizde yüksek hızlı bir Samsung NVMe SSD bulunmasına rağmen, Raspberry Pi 5'in tek PCIe yolunun AI HAT+ (Hailo-8) tarafından kullanılması zorunluluğu nedeniyle, SSD'nin USB 3.0 adaptör üzerinden harici depolama olarak kullanılmasına veya sistemin MicroSD üzerinden koşturulmasına karar verilmiştir.


### 💾 Depolama Çözümü (Kesinleşen)
- **Cihaz:** Samsung PM981 256GB NVMe SSD
- **Bağlantı:** Ugreen USB 3.1 Gen2 Type-C M.2 NVMe Kutusu
- **Performans:** UASP desteği ile USB 3.0 üzerinden yüksek hızlı boot ve veri erişimi.
- **Strateji:** PCIe yolu Hailo AI modülüne ayrılmış, ana işletim sistemi ve LLM modelleri SSD üzerine kurulmuştur.
