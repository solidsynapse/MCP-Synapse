# MCP Synapse - Master Plan ve SSOT Durum Raporu

> MASTERPLAN_V2 IS NOT SSOT (vision/reference only).
> Bağlayıcı SSOT dosyaları: docs/DECISIONS.md, docs/STATUS.md, docs/TASKS.md.
> Scope lock: Phase 2’de UI (Flet dahil) kapsam dışıdır ve UI code changes yasaktır (D-019).
> MVP’ye kadar ilerleme yalnız headless kanıt hattı ile doğrulanır (pytest + mcp probe + smoke_tests + evidence pack).


## 1. Yönetici Özeti ve Ürün Konumlandırması

MCP Synapse, IDE'lerin (Cursor, Windsurf, Cline vb.) yerleşik olarak desteklemediği yapay zeka sağlayıcılarını entegre eden, yerel (local-first) ve güvenli bir Model Context Protocol (MCP) ağ geçididir. Uygulama, salt bir proxy olmanın ötesine geçerek; LLMOps (gözlemlenebilirlik), FinOps (maliyet optimizasyonu) ve hata toleransı (resilience) katmanları sunarak geliştiricilerin API maliyetlerini ve sistem tutarlılığını yönetmelerini sağlar. Ürün, "Açık Çekirdek" (Open Core) modeliyle dağıtılacak olup, kurumsal düzeydeki analiz ve optimizasyon araçları premium lisanslama ile sunulacaktır.

## 2. Teknik Mimari

Sistem, kararlılık ve düşük kaynak tüketimi ilkelerine göre iki ana bileşene ayrılmıştır:

* **Çekirdek Motor (Backend):** Python 3.11.9 (mevcut runtime) + SQLite (mevcut). HTTP/SSE API katmanı (ör. FastAPI) hedeflenen adaydır ve SSOT kararı olmadan bağlayıcı değildir. Bu katman, "Sidecar" (yan süreç) olarak arka planda çalışır ve yönlendirme (routing), veritabanı yazımları ve sağlayıcı adaptörlerini yönetir.
* **Arayüz (Thin Shell Frontend):** Tauri + Svelte + Shadcn UI hedeflenen aday UI stack’idir; UI en son MVP adımı olarak inşa edilir. Arayüz, üretim yolunda (production path) doğrudan sağlayıcı çağırmaz; yalnızca konfigürasyon işlemlerini ve metrik gösterimini (dispatch and render) üstlenir. Arayüz, üretim yolunda (production path) doğrudan sağlayıcı çağırmaz; yalnızca konfigürasyon işlemlerini ve metrik gösterimini (dispatch and render) üstlenir.

## 3. Detaylı Özellik Listesi (Feature List)

### 3.1. Çekirdek Özellikler (Core / Ücretsiz)

* **Evrensel Köprüleme (Universal Bridge):** Native MCP desteği bulunmayan modellerin IDE'lere standart bir MCP sunucusu olarak bağlanmasını sağlayan sağlayıcı soyutlama katmanı.
* **Deterministik Yönlendirme Katmanı (Pipeline V1):** Çekirdek mimaride gizli yeniden deneme (retry), geri çekilme (backoff) veya sessiz geri dönüş (silent fallback) mekanizmaları bulunmaz; tüm hatalar kullanıcıya açıkça yansıtılır.
* **Açık Ağ İzinleri (Explicit Opt-in):** Gerçek ağ çağrıları içeren sağlayıcılar (örneğin Bedrock ve Hugging Face), kullanıcı tarafından açıkça yetkilendirilmeden çalıştırılmaz.
* **Güvenli Kimlik Yönetimi:** API anahtarları yapılandırma dosyalarında (config.json) düz metin olarak saklanmaz; işletim sistemi anahtarlığından (keyring) veya yerel dosya yollarından şifreli olarak okunur.
* **"Copy Config" UX:** Kullanıcıların oluşturdukları MCP köprü yapılandırmalarını tek tıklamayla panoya kopyalayıp IDE ayar dosyalarına yapıştırmalarını sağlayan arayüz akışı.
* **Lokal Telemetri ve Gözlemlenebilirlik:** Veritabanına (SQLite) her isteğin durumu (status), hata türü (error_type), gecikme süresi (latency_ms), giriş/çıkış token sayıları ve USD bazlı maliyeti yerel olarak kaydedilir. Prompt ve model yanıtı (payload) güvenlik ve depolama kısıtları nedeniyle kaydedilmez.
* **Kullanım ve KPI Paneli (Usage Dashboard):** Veritabanından beslenen; toplam istek, başarı oranı, toplam maliyet ve ortalama gecikme verilerini filtreli (sağlayıcı ve tarih bazlı) olarak sunan arayüz modülü.

### 3.2. Premium Özellikler (Pro / FinOps & Resilience)

* **Interceptor (JSON Syntax Repair):** Modellerden dönen ve IDE istemcisini çökertebilecek hatalı fonksiyon çağrılarını (eksik tırnak, trailing comma vb.) hafif Regex/parse kütüphaneleriyle anında onaran ve kaydedilen maliyeti UI üzerinde raporlayan direnç katmanı.
* **Persona Lite (Sistem Prompt Enjeksiyonu):** IDE'den gelen ana bağlamı bozmadan, statik JSON tabanlı kuralları (örn. kodlama standartları) isteklere arka planda deterministik olarak enjekte eden modül.
* **FinOps Context Caching:** Desteklenen sağlayıcıların (Anthropic, Gemini) bağlam önbellekleme (context caching) API özelliklerini yönlendirici (router) seviyesinde yöneterek token maliyetlerini minimize eden optimizasyon katmanı.
* **Budget Guard (Kota Kalkanı):** IDE tarafında oluşabilecek sonsuz döngü hatalarını engellemek amacıyla, her bir köprü/ajan için günlük harcama (USD) veya token sınırları belirleme özelliği.
* **Dışa Aktarım (Export):** Kullanım metriklerinin (kullanıcı promptları hariç) kurumsal raporlama süreçleri için deterministik kurallara bağlı kalarak CSV formatında dışa aktarımı.

## 4. Sağlayıcı Entegrasyon Fazları (Provider Waves)

Pazara çıkış (GTM) stratejisi doğrultusunda entegrasyonlar üç ana dalgada gerçekleştirilecektir:

1. **Dalga 1 - Kurumsal Ağ Geçitleri:** IDE'lere bağlanması karmaşık olan majör bulut hizmetleri; Google Vertex AI, Microsoft Azure OpenAI, Amazon Bedrock, Hugging Face ve Google AI Studio.
2. **Dalga 2 - Yerel Odak:** Çevrimdışı çalışma ve maksimum gizlilik talep eden kullanıcılar için Ollama entegrasyonu.
3. **Dalga 3 - FinOps ve Analitik Odaklı Eklentiler:** Hali hazırda IDE'ler tarafından desteklenen ancak uygulama üzerinden LLMOps ve bütçe yönetimi avantajı sağlamak amacıyla entegre edilecek olan OpenAI, Anthropic (Claude) ve Groq.

## 5. SSOT (Single Source of Truth) Durum Analizi

Projenin temel belgeleri (STATUS.md, TASKS.md, DECISIONS.md) incelendiğinde, Faz-2'nin (Çekirdek Ürünleştirme ve Headless MVP) büyük oranda tamamlandığı ve katı kurallara bağlandığı görülmektedir:

* **Faz-2 Geçiş Kapıları (Done Gates):** MCP Tool Discovery (`initialize`, `tools/list`, `tools/call`) sözleşmesi, arayüz olmadan (headless) test edilmiş ve ham JSON-RPC dökümleriyle doğrulanarak PASS statüsü almıştır.
* **MVP.1 Sürümü:** Google Vertex ve Azure OpenAI sağlayıcıları için belirlenen entegrasyon testleri (smoke tests) başarıyla tamamlanmıştır.
* **Veritabanı Sözleşmesi (D-004):** Arayüzün kullanım (Usage) sekmesinde göstereceği verilerin ve KPI'ların (başarı oranı, gecikme, hata türleri) doğrulanabilir tek kaynak olarak yapılandırılması SSOT ile kilitlenmiştir.
* **Kod Standartları ve İzolasyon:** Faz-2 boyunca UI kod değişiklikleri D-019 kararı ile kesin olarak yasaklanmış (Scope Lock), üretilen tüm doğrulamalar test (pytest) ve CLI araçları ile sağlanmıştır.
* **Kapanış İşlemleri:** T3.A ve T3.B (Güvenli kod silme) görevleri kapsamında `.pyc` ve `__pycache__` gibi kullanılmayan derlenmiş dosyaların temizliği gerçekleştirilmiştir.

## 6. Gelecek Faz Planlaması

Mevcut SSOT durumu ve güncellenmiş Master Plan ışığında projenin ilerleme adımları şu şekildedir (UI en son MVP adımıdır):

* **Phase 3 - Headless Core Expansion (UI yok):** Sağlayıcı dalgaları ve premium özellikler yalnız headless hat üzerinden ilerletilir. Premium kalemler önce **contract-first (docs-only)** olarak tanımlanır (determinism + explicit opt-in + kanıt formatı), implementasyon sonradan task/evidence ile açılır.
* **Phase 4 - Paketleme / Dağıtım / GTM Hazırlığı (headless kanıtlı):** Windows/macOS/Linux paketleme adımları, smoke/QA komutları ve rollback prosedürleri standardize edilir. Arka plan çalışma/sistem tepsisi gibi operasyonel yüzeyler deterministik şekilde kanıtlanır.
* **Phase 5 - UI Thin Shell (Tauri + Svelte):** UI yalnız “configure + dispatch + render” katmanı olarak en son inşa edilir. UI içinde provider call veya core business logic bulunmaz. Flet prototipi “historical” olarak kalır (D-019 scope lock).
************

## Ek 1: Teknik Stack
## Project Notes (SSOT-derived, non-binding)
> This section is informational only. The binding source of truth is in docs/DECISIONS.md, docs/STATUS.md, docs/TASKS.md.

### Compliance baseline (BYOK + local-only)
- BYOK + local-only by default; no key pooling; no SaaS proxy mode unless explicitly approved.
- Providers with ambiguous/strict ToS remain contract-only until written clarification/approval is captured as evidence.

### Phase 3 hardening (headless-first)
- UI is a thin shell: config + dispatch + render only. No provider calls in UI production path.
- Headless proofs completed:
  - Copy Config: deterministic output, no secrets, pytest PASS
  - CSV Export: headless export + deterministic hash, UI dispatch only, pytest PASS
  - Budget Guard: monitor-only (no enforcement), deterministic report, pytest PASS

### Provider roadmap update
- Google AI Studio: deferred to post-MVP; blocked pending written ToS clarification/approval.
- Ollama: feasibility proven (fail-fast when unreachable; reachable smoke PASS).
- OpenAI / Anthropic / Groq: contract-first tasks added; OpenAI feasibility smoke queued.

## Roadmap (SSOT-derived, non-binding)
> Informational only. Binding truth remains in docs/DECISIONS.md, docs/STATUS.md, docs/TASKS.md.

1) LM Studio feasibility (PR7.I1) — local OpenAI-compatible server smoke (non-streaming)
2) Premium (contract-first): Interceptor (P3.P1), Persona Lite (P3.P2), Context caching (P3.P3)
3) OpenAI online feasibility (PR3.I1) — requires BYOK key
4) UI rewrite prep → UI (thin shell; last major build step)
5) Documentation closeout: User Guide + legal pack (P3.LG1)
