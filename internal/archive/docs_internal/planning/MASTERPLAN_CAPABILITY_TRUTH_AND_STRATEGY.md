# MASTERPLAN Capability Truth and Strategy (Non-SSOT)

> Bu belge SSOT degildir. Ama amaci, eski master plan vizyonunu bugunku gercek urun kapasitesi ile hizalamak ve calisilabilir bir strateji tabani olusturmaktir.
> Kaynaklar: handoff/.../MASTERPLAN_V2__aligned.md, docs/MCP_Router_Master_Plan.md, docs/STATUS.md, docs/TASKS.md, docs/DECISIONS.md, mevcut repo davranisi.

## 1) Kisa Sonuc (Executive Snapshot)

- Uygulama artik "yalniz prototip" seviyesinde degil; Core + UI Thin Shell birlikte calisan bir urun omurgasi var.
- Eski planlardaki bircok cekirdek kalem gercekte teslim edildi (Connections, Usage, Dashboard, Persona Lite, Optimizations, Interceptors, Budget monitor-only).
- Acik kalan ana stratejik bosluklar:
  - Cross-provider maliyet dogrulugu (su an provider'a gore degisken),
  - Gelismis routing/chain/memory tarafinin urune alinmasi,
  - Paketleme, dagitim, release hardening, guvenlik audit.
- SSOT bakisiyla kritik not: P5.14F PASS, P5.14C REVALIDATE, P5.14E STALE_SSOT.

## 2) Eski Master Planlara Gore Karsilama Orani (Genel)

- MASTERPLAN_V2 cekirdek + premium vizyonunun bugun karsilanma orani: yuksek (yaklasik 70-80% cekirdek, 50-60% premium-lite).
- MCP_Router_Master_Plan fazlarina gore karsilanma:
  - Phase 0/1 sinifi (stabilizasyon + usage reliability): buyuk oranda tamam.
  - Phase 2 (provider adapter seam): yapisal olarak var.
  - Phase 3 (universal bridge genisleme): kismi.
  - Phase 4/5 (chain editor + memory studio): henuz yok / roadmap adayi.

Bu oranlar kesin release metrikleri degil; kanitli feature varlik ve davranis olgunluguna gore verilmis operasyonel tahmindir.

## 3) Capability Truth Matrix (Plan vs Bugun)

| Capability | Eski planlarda | Bugun durum | Gercek not |
|---|---|---|---|
| Universal bridge omurgasi | Var | PARTIAL->DONE | ProviderFactory + Pipeline v1 var; birden fazla provider kayitli.
| Deterministic pipeline | Var | DONE | Hata ve status kaydi deterministik; gizli retry/fallback iddiasi yok.
| Connections lifecycle (create/update/preflight/start/stop/delete) | Var | DONE | UI dispatch ve manager op seti aktif.
| Copy Config UX | Var | DONE | Connections UI + manager copy_config + dry-run trace mevcut.
| Usage telemetry (status/latency/tokens/cost/request_id/provider/model) | Var | DONE | DB schema ve usage.recent ciktilari bu alanlari tasiyor.
| Usage export CSV | Var | DONE | Save dialog + filtre propagasyonu + csv serialization mevcut.
| Dashboard KPI + trend + breakdown + alerts | Var | DONE | dashboard.get_state ve son polish turlari PASS.
| Persona Lite (deterministic injection) | Var | DONE | Persona state + runtime inject zinciri mevcut.
| Optimizations (context cache + dedup) | Var | DONE | Config state + runtime apply + dedup hit yolu mevcut.
| Interceptor JSON syntax repair | Var | DONE | Runtime apply path mevcut.
| Budget Guard | Var | PARTIAL (monitor-only) | Bilincli karar: enforcement deferred, yalniz alert/render.
| Request bazli maliyet tahmini (tum providerlar) | Ima ediliyor | PARTIAL | Vertex cost dolduruyor; OpenAI/Azure/Ollama cost_usd None.
| Chain Editor v1 | Var | NOT DELIVERED | UI route/backend feature gorunmuyor.
| Advanced routing (fan-out/branch/retry/failover) | Var | NOT DELIVERED | Bu seviye urun davranisi kanitli degil.
| Persona/Memory Studio (pro seviye) | Var | PARTIAL | Persona Lite var; memory/embedding/studio yok.
| Export packs (usage/chain/persona) | Var | PARTIAL | Usage CSV var; chain/persona pack export yok.
| Auto-update / signed installer convenience | Var | NOT DELIVERED | Bu kapsamda kanitli teslim yok.

## 4) Net Teknik Gerceklik: Neleri Yapiyoruz / Neleri Yapamiyoruz

### A) Bugun guvenle yaptiklarimiz

1. UI thin shell gercekten dispatch-and-render modelinde calisiyor.
2. Connections ve Usage operasyonlari urun akisinda calisiyor.
3. Dashboard canli metrik/gorsel kompozisyonu urun seviyesinde kullanilabilir durumda.
4. Persona, Optimizations, Interceptors, Budget monitor semantik olarak urune entegre.
5. Evidence-first calisma modeli ile geri donus riski azaltildi.

### B) Bugun sinirli/yarim olanlar

1. Cross-provider cost dogrulugu esit seviyede degil.
   - Vertex tarafi cost hesapliyor.
   - OpenAI/Azure/Ollama tarafinda cost_usd su an None donuyor.
2. Budget Guard enforcement bilincli olarak devre disi (monitor-only).
3. Chain/advanced routing/memory gibi "pro orchestration" katmani henuz urunde yok.

### C) Bugun yapmadiklarimiz (ama roadmap adayi)

1. Chain Editor (wizard -> sonra graph).
2. Memory Studio / local embeddings.
3. Export bundles (chain/persona pack).
4. Paketleme, signed installer, auto-update, dagitim operasyonlari.
5. Sistematik performance + security hardening turu.

## 5) Eski Planlardan Bugune Duzeltme (Nerede Ayrildik?)

- MASTERPLAN_V2 tarihsel olarak "UI en son" diyor; bugun ise UI aktif urun katmani olarak oldukca ileride.
- Bu ayrisma negatif degil: fiili ilerleme, plan sirasindan daha hizli sekilde UI+core paraleline kaymis.
- Yeni strateji bu gercegi kabul etmeli: artik "UI var mi?" sorusundan "release hardening + capability depth" sorusuna gecildi.

## 6) vCurrent Strateji (Guvenilir Yol)

### Faz S1 - Gate closure ve scope temizligi (kisa)
- P5.14C: REVALIDATE alanini bilincli carry-forward ile daralt.
- P5.14E: STALE_SSOT alanini implementasyon gelene kadar acik tut.
- Her menu kapanisinda minimal SSOT sync + evidence index.

### Faz S2 - Capability depth (urun degerini arttiran teknik adim)
- Cross-provider cost normalizasyonu:
  - "unknown/none" durumunu acik semantik ile ele al,
  - mumkun olan providerlarda deterministic cost mapper ekle.
- Usage/analytics katmaninda provider bazli veri kalite gostergesi ekle (maliyet kesinligi gibi).

### Faz S3 - Hardening (release adayi oncesi)
- Debugging / regression / edge-case stabilizasyonu.
- Security audit (credential flow, local storage, dispatch surface, error handling).
- Performance turu (UI rendering, query path, cache/dedup davranisi).

### Faz S4 - Productization
- Packaging + update strategy + rollback proseduru.
- Release checklist + known issues + support docs.
- Public roadmap ayrimi: "current delivered" vs "next wave".

## 7) Roadmap Candidate List (SSOT disi, aday havuz)

1. Chain Editor v1 (sequential wizard).
2. Advanced routing policy seti (fan-out/branch/retry/failover).
3. Memory Studio (lite->pro).
4. Export packs (usage + chain + persona).
5. Cross-provider cost intelligence katmani.
6. Release operations: installer signing, update kanali, rollback automation.

## 8) Karar Icin Onerilen Yonetim Kurali

- Bundan sonra her yeni roadmap maddesi su filtreyle alinmali:
  1) Uygulama bugun bunu yapabiliyor mu?
  2) Evidence ile dogrulanmis mi?
  3) SSOT gate'ine nasil baglanacak?
  4) Builder'a verilecek en dar implementasyon dilimi ne?

Bu filtre korunursa proje hiz kaybetmeden, tekrar geri dusmeden release-ready seviyeye ilerler.
