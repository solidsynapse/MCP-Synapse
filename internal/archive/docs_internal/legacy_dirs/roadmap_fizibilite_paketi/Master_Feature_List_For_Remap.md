# Master Feature List For Remap (Working Draft)

Amac: Bu dosya, mevcut dokumantasyona gore tum feature seti tek yerde toplansin diye olusturuldu.
Bu asamada listeleme yapilir; final remap ve numeric gate bir sonraki adimdir.

Kullanım notu:
- Bu dosyaya unutulan maddeleri ekleyebilirsin.
- Her madde tek satir olmalı.
- "Kisa Not" alani release/migration onceligini tek cumleyle belirtir.

## A) Release Core / Mevcut Omurga

| ID | Feature | Kisa Not |
|---|---|---|
| F-001 | Pipeline V1 merkezi execution yolu | Release icin şart; core stabil kalmali. |
| F-002 | ProviderFactory/provider seam | Release icin şart; provider bagimliligini core'dan ayirir. |
| F-003 | Connection lifecycle (create/edit/delete/start/stop) | Release icin şart; temel operasyon akisidir. |
| F-004 | Connection preflight | Release icin şart; hatayi erken yakalar. |
| F-005 | Copy Config (core-generated) | Release icin şart; deploy/onboarding akisini hizlandirir. |
| F-006 | Usage Summary (dispatcher-backed) | Release icin şart; temel gorunurluk metrigi. |
| F-007 | Usage History (dispatcher-backed) | Release icin şart; log gozlemi ve denetim izi icin kritik. |
| F-008 | Usage filters (provider/date/model/tokens/sort) | Release icin şart; operasyonel analiz verimliligi icin gerekli. |
| F-009 | Usage CSV export (save dialog + filter propagation) | Release icin şart; raporlama/export beklentisini karsilar. |
| F-010 | Dashboard KPI cards | Release icin şart; hizli durum ozeti verir. |
| F-011 | Dashboard cost trend chart (30-day) | Release icin şart; maliyet hareketini gorunur yapar. |
| F-012 | Dashboard cost breakdown chart | Release icin şart; provider dagilimini gosterir. |
| F-013 | Quick Health Alerts panel | Release icin şart; kritik sinyal panelidir. |
| F-014 | Recent Requests table (dashboard) | Release icin şart; son akis denetimini saglar. |
| F-015 | Top Expensive Requests card | Release icin şart; maliyet agir requestleri one cikarir. |
| F-016 | Global refresh propagation | Release icin şart; ekranlar arasi tutarlilik saglar. |
| F-017 | Persona Lite state + runtime binding | Release icin şart; policy etkisini runtime'a tasir. |
| F-018 | Optimizations (context cache + dedup) runtime effect | Release icin şart; performans ve tekrar azaltim degeri uretir. |
| F-019 | Interceptors runtime effect | Release icin şart; policy akisinda temel kontrol noktasidir. |
| F-020 | Budget Guards monitor-only alerts | Release icin şart; D-031'e uyumlu monitor davranisi korunur. |
| F-021 | Settings get/set + persistence + validation | Release icin şart; sistem davranisini guvenli konfigure eder. |
| F-022 | Thin-shell UI dispatch pattern | Release icin şart; core merkezli davranisi korur. |
| F-023 | Deterministic error payload contract | Release icin şart; debug ve destek surecini standartlar. |
| F-024 | Runtime terminal proof discipline (interceptor/dedup/cache) | Release icin şart; wiring iddialarini kanitla tutar. |
| F-025 | Global layout polish (right-edge jitter control) | Release kalitesi icin gerekli; UX stabilitesi etkiler. |
| F-055 | Legal/Compliance Minimum Pack (LC-MIN-01) | Release icin şart; minimum GDPR/telemetry/retention kalkanini saglar. |
| F-056 | User Documentation Pack (DOCS-MIN-01) | Release icin şart; user guide + known issues + feature wiki yardimini saglar. |

## B) Acik / Kosullu (Current Truth Carry-Forward)

| ID | Feature | Kisa Not |
|---|---|---|
| F-026 | P5.14C residual usage/connections reconfirm | Release oncesi netlestirilmeli; uzun REVALIDATE tasinmamali. |
| F-027 | Tooltip/helper system | Migration sonrasi onerilir; su an STALE_SSOT. |
| F-028 | Budget enforcement toggle (block/throttle) | Migration sonrasi; D-031 geregi su an devreye alinmaz. |
| F-029 | Full-surface destructive confirmations | Release'e yakin tek turde yapilmali; veri kaybi riski kontrollu olmali. |
| F-030 | Git init/history governance | Release hardening icin onerilir; denetim izi kalitesini artirir. |
| F-057 | Audit log (basic) | Migration-ready; v1.1'de denetim izi ve operasyonel izleme gucunu artirir. |
| F-058 | Performance optimization pack (async + cache) | Migration-ready; v1.1'de yanit suresi/throughput kazanimi hedefler. |

## C) Maliyet Modulu (Kritik Stratejik Paket)

| ID | Feature | Kisa Not |
|---|---|---|
| F-031 | cost_source field (ACTUAL/ESTIMATED/UNKNOWN) | Release icin guclu aday; cost yorum hatasini azaltir. |
| F-032 | pricing_version + pricing_timestamp | Migration-ready; izlenebilirlik ve audit kalitesini artirir. |
| F-033 | estimation_confidence (LOW/MEDIUM/HIGH) | Migration-ready; karar kalitesini veri guven seviyesine baglar. |
| F-034 | UI cost badge (Actual/Estimated/Unknown) | Release icin guclu aday; kullaniciya dogru beklenti verir. |
| F-035 | Provider quality score for cost reliability | Migration sonrasi onerilir; once temel contract oturmali. |
| F-036 | Cross-provider cost normalization layer | Migration-ready; kritik ama kontrollu fazda alinmali. |
| F-037 | Pricing snapshot refresh governance | Migration-ready; sessiz fiyat drift riskini azaltir. |

## D) Domain-Agnostic Donusum Cekirdegi (Hedef Mimari)

| ID | Feature | Kisa Not |
|---|---|---|
| F-038 | Core RequestEnvelope v0 | Migration-ready; donusumun ana kontrat tasidir. |
| F-039 | Core ExecutionResult v0 | Migration-ready; uyumluluk icin zorunlu cikis kontrati. |
| F-040 | Core EventEnvelope v0 | Migration-ready; observability normalizasyonu icin temel. |
| F-041 | Compatibility adapter (legacy payload -> v0) | Migration-ready; non-breaking gecisin ana guvencesi. |
| F-042 | Hook chain registry (pre_context->policy->routing->execution->post) | Migration-ready; plugin/hook mimarisinin cekirdegi. |
| F-043 | Hook semantics (sync/async, timeout, cancel, fail policy) | Migration-ready; determinism riskini kapatir. |
| F-044 | Policy modules via executable hooks | Migration-ready; state-only modelden runtime etkisine gecis. |
| F-045 | Provider metadata contract cleanup | Migration-ready; provider-specific dallari core'dan iter. |
| F-046 | Observability capability/event schema | Migration-ready; migration doneminde cift-sema ile ilerlemeli. |
| F-047 | Dispatcher op registry modularization | Migration-ready; monolit op-chain riskini azaltir. |

## E) Productization / Roadmap Candidate Havuzu

| ID | Feature | Kisa Not |
|---|---|---|
| F-048 | Chain Editor v1 | Post-migration onerilir; core contract oturmadan erken. |
| F-049 | Persona/Memory Studio (pro-level) | Post-migration onerilir; domain adapter bagimliligi yuksek. |
| F-050 | Export packs (usage + chain + persona) | Post-migration onerilir; once temel export contract netlesmeli. |
| F-051 | Domain adapter pack modeli | Post-migration onerilir; execution-fabric tabani uzerinde olgunlasir. |
| F-052 | Enterprise compliance/audit packs | Post-migration onerilir; observability ve policy altyapisi olgunlasmali. |
| F-053 | Advanced analytics / observability pack | Post-migration onerilir; event schema netligi onkosul. |
| F-054 | Packaging/update/rollback productization | Release hardening icin şart; teknik borc azaltimindan bagimsiz yurur. |

## F) Manuel Ekleme Alani (Senin icin)

Bu alana unutuldugunu dusundugun feature satirlarini ekleyebilirsin.
Onerilen format:

| ID | Feature | Kisa Not |
|---|---|---|
| F-XXX | <feature_adi> | <release/migration tek cumle notu> |

---

Kaynak havuzu (bu taslakta kullanilan):
- docs/STATUS.md
- docs/TASKS.md
- docs/CurrentState_WorksLeft.md
- docs/MASTERPLAN_CAPABILITY_TRUTH_AND_STRATEGY.md
- docs/maliyet_modulu_calisma/Maliyet_Modulu_Fizibilite_On_Degerlendirme.md
- docs/domain-agnostic-fizibilite/Execution_Fabric_Fizibilite_On_Degerlendirme.md
- docs/DECISIONS.md
