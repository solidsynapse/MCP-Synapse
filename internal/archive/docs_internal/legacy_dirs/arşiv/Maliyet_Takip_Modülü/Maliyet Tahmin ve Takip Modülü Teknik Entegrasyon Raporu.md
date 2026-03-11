**MCP Router Uygulaması**  
**Maliyet Tahmin ve Takip Modülü Teknik Entegrasyon Raporu**  

**Hazırlayan:** [Senin Adın / COINer]  
**Tarih:** 03 Mart 2026  
**Versiyon:** 1.0  
**Hedef Kitle:** Süpervizör / Teknik Lider / Proje Paydaşı  

---

### 1. Özet (Executive Summary)

MCP tabanlı router/gateway uygulamasının (Windows masaüstü power tool) eksik kalan tek parçası olan **“her provider’a giden LLM request’inin önceden tahmini maliyeti + çağrı sonrası actual maliyet takibi”** özelliği, **LiteLLM Python SDK’sinin sadece utils katmanı** olarak entegre edilecektir.

- **Seçilen yaklaşım:** LiteLLM’i ayrı bir gateway/proxy olarak değil, **görünmez bir iç hesaplama motoru** (cost engine) olarak kullanmak.
- **Mimari prensip:** Thin Shell UI + Sağlam Core + Plugin Tabanlı genişletilebilirlik.
- **Kullanıcı deneyimi:** LiteLLM adı hiçbir yerde görünmeyecek; tüm güncellemeler “API Maliyet Hesaplamaları Güncellemesi” olarak sunulacak.
- **Kurulum:** Kullanıcı tek komutla (`pip install -r requirements.txt` veya .exe installer) tüm uygulamayı kuracak; ekstra hiçbir şey yüklemeyecek.
- **Bakım yükü:** Yeni model/fiyat geldiğinde LiteLLM otomatik güncellenir; kullanıcı settings’ten “Güncellemeleri Denetle” butonu ile manuel onay verir.

Bu yaklaşım **en düşük bakım yükü**, **en yüksek tutarlılık** ve **sıfır operasyonel ek yük** sağlar.

---

### 2. Giriş ve Amaç

**Amaç:**  
Uygulama içinde her MCP tool invocation / LLM çağrısı öncesi **gerçekçi tahmini maliyet** hesaplamak, bütçe guard’ları çalıştırmak, actual maliyeti loglamak ve USAGE tablolarına yazmak.

**Kapsam:**  
- İlk etap provider’lar: Google Vertex AI (Gemini), Microsoft Azure OpenAI, Amazon Bedrock  
- İkinci etap: Hugging Face, OpenAI, Anthropic, Groq  
- Multi-modal (image/video), tool-heavy prompt’lar ve MCP protocol tam desteklenecek.

---

### 3. Değerlendirme ve Seçilen Çözüm

**Değerlendirilen Alternatifler**

| Alternatif                  | Bakım Yükü | Tutarlılık | Kod Değişikliği | Yasal / Lisans | Operasyonel Yük | Puan |
|----------------------------|------------|------------|-----------------|----------------|-----------------|------|
| Sıfırdan kendi registry + tokenizer | Yüksek     | Orta       | Çok yüksek      | Yok            | Yok             | 4/10 |
| LiteLLM Proxy (ayrı servis) | Orta       | Yüksek     | Yüksek          | MIT + Enterprise | Yüksek          | 6/10 |
| **LiteLLM SDK (utils-only)** | **Çok Düşük** | **Çok Yüksek** | **Çok Düşük**   | **MIT (tamamen serbest)** | **Sıfır** | **10/10** |

**Neden LiteLLM SDK?**  
- MIT lisansı → ücretli ticari uygulamada %100 serbest (enterprise lisansa gerek yok).  
- 100+ provider, canlı model fiyat haritası (`model_prices_and_context_window.json`), provider-specific tokenizer (Vertex countTokens, Anthropic tokenizer, tiktoken vb.).  
- Sadece `completion_cost()` ve `token_counter()` fonksiyonları kullanılacak.  
- LiteLLM Proxy’den tamamen bağımsız; hiçbir ayrı sunucu/process yok.

---

### 4. Teknik Mimari

**Plugin Yapısı (Proje Felsefesiyle Tam Uyumlu)**

```
plugins/
└── cost_estimator/
    ├── __init__.py
    ├── cost_engine.py          # ApiCostCalculator (LiteLLM wrapper)
    ├── model_mapping.py        # MODEL_TO_LITELLM dict
    ├── update_checker.py       # Kullanıcıya görünen güncelleme mantığı
    └── config.py
```

**Core Entegrasyonu (Minimal Dokunuş)**  
Tüm LLM invocation noktalarına (mevcut provider SDK çağrıları) sadece iki hook eklenecek:

```python
estimated = cost_engine.estimate(model_key, messages, tools, max_tokens)
# ... bütçe kontrolü ...
response = provider_call(...)
actual = cost_engine.actual(response)
```

**Görünmezlik Katmanı**  
- Sınıf adı: `ApiCostCalculator` veya `CostEngine`  
- Kullanıcıya gösterilen tüm mesajlar: “API Maliyet Hesaplamaları”  
- LiteLLM adı sadece log dosyalarında ve `THIRD_PARTY_LICENSES.txt` dosyasında geçecek.

---

### 5. Güncelleme ve Kullanıcı Deneyimi (Windows Masaüstü Özel)

**Settings → Güncellemeler Sekmesi**  
- Checkbox: “Güncellemeleri otomatik denetle (önerilir)”  
- Buton: “Şimdi Güncellemeleri Denetle”  
- Mesaj örnekleri:
  - “API maliyet hesaplamaları için yeni güncelleme mevcut (daha fazla model ve güncel fiyatlar eklendi)”
  - “Güncelleme tamamlandı. API maliyet tahminleri yenilendi. Uygulamayı yeniden başlatın.”

**Güncelleme Akışı**  
Kullanıcı butona basınca → sessiz `pip install --upgrade litellm` → başarı mesajı (LiteLLM adı görünmez) → restart önerisi.

**Otomatik Senkronizasyon**  
Yeni fiyat/model LiteLLM kütüphanesine eklendiği anda, kullanıcı “Denetle” dediğinde uygulamaya yansır. Senin ekstra kod değişikliği yapmana gerek kalmaz.

---

### 6. Lisans ve Yasal Uyum

- LiteLLM ana SDK → MIT License (ticari kullanım serbest).  
- Kullanılan parçalar (completion_cost, token_counter, model map) → tamamen açık kaynak.  
- Gereken tek şey: `THIRD_PARTY_LICENSES.txt` dosyasına kısa kayıt eklemek.  
- BerriAI’nin resmi dokümantasyonu ve GitHub sayfası ticari kullanımı açıkça desteklemektedir.

---

### 7. Avantajlar ve Riskler

**Avantajlar**
- Bakım yükü minimum (ayda 1-2 kez dependency upgrade).
- Token hesaplama doğruluğu çok yüksek (provider-specific tokenizer).
- Plugin mimarisiyle ileride her yeni feature aynı yöntemle eklenebilir.
- Kullanıcı tamamen “kendi uygulaması” hisseder.
- Tek installer, sıfır ekstra kurulum.

**Riskler ve Mitigasyon**
- LiteLLM’de nadir breaking change → Mitigasyon: `litellm>=1.55,<2.0` constraint + test suite.
- Windows UAC/antivirüs → Mitigasyon: Sessiz upgrade + kullanıcı onayı + loglama.
- Bağımlılık şişmesi → Mitigasyon: Sadece gerekli fonksiyonlar import edilir (lazy loading).

---

### 8. Implementasyon Adımları (A’dan Z’ye)

1. `plugins/cost_estimator/` klasörü oluştur.
2. `ApiCostCalculator` sınıfını yaz (wrapper).
3. MODEL_TO_LITELLM mapping dict’ini oluştur.
4. Mevcut LLM çağrı noktalarını tespit edip pre/post hook ekle.
5. `requirements.txt` → `litellm>=1.55` satırı ekle.
6. `THIRD_PARTY_LICENSES.txt` oluştur.
7. Settings ekranına “Güncellemeleri Denetle” UI’sini ekle.
8. Update checker ve custom mesaj mantığını yaz.
9. Test: Vertex, Azure, Bedrock + multi-modal + tool-heavy prompt’lar.
10. Dokümantasyon ve changelog güncelle.

Tahmini süre: 1-1.5 iş günü (mevcut kod %95 hazır olduğu için).

---

### 9. Sonuç ve Tavsiye

Bu entegrasyon yaklaşımı, projenin “Thin Shell + Sağlam Core + Plugin” felsefesiyle **mükemmel uyumludur**.  
LiteLLM SDK’sini görünmez bir “maliyet hesaplama motoru” olarak kullanmak, hem teknik olarak en temiz hem de ticari/operasyonel olarak en düşük riskli çözümdür.

**Tavsiye:**  
Hemen implementasyona geçilsin. Codex CLI’ye verilecek prompt hazırdır; isterseniz bir sonraki adımda onu da sunabilirim.

Herhangi bir bölümde ek detay veya değişiklik isterseniz lütfen belirtin.

---

**Ekler**  
- Ek-1: Örnek `ApiCostCalculator` class şablonu  
- Ek-2: Kullanıcıya gösterilecek mesaj kütüphanesi  
- Ek-3: Güncelleme akış diyagramı (mermaid)

Bu raporu doğrudan Word/PDF’e kopyalayıp sunabilirsiniz.  
Hazırsanız implementasyon prompt’unu veya örnek kod şablonlarını da hazırlayayım.