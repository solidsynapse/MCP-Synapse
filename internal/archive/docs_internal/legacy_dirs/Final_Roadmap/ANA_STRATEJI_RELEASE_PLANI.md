# ANA STRATEJI RELEASE PLANI (Tek Dosya Takip Belgesi)

Durum: Operasyonel ana rehber
Kapsam: Bulundugumuz durum, mevcut kabiliyetler, release'e kadar teknik evreler, feature evreleme, modul entegrasyon plani
Not: Bu belge SSOT degildir; SSOT pusulasi ile birlikte kullanilir.

## 1) Bulundugumuz Nokta (Kisa Current Snapshot)

- UI + wiring yuzeylerinin buyuk bolumu calisir durumda ve PASS tabaninda.
- P5.12C PASS, P5.14F PASS, P5.14D PASS, P5.14A/B PASS.
- Acik kalan kontrollu alanlar:
  - P5.14C REVALIDATE (bilincli carry-forward)
  - P5.14E STALE_SSOT (helper sistemi implementasyonu yok)
- Budget guard davranisi normatif olarak monitor-only kilidinde (D-031).

Sonuc: Urun prototipten cikti; release hardening + karar kilitleme evresindeyiz.

## 2) Mevcut Kabiliyetler (Calisan Omurga)

### 2.1 Core / Runtime
- Pipeline V1 merkezi execution yolu
- Provider seam (ProviderFactory + provider adapter yapisi)
- Deterministic dispatch/error contract omurgasi

### 2.2 Uygulama Yuzeyleri
- Connections lifecycle: create/edit/delete/start/stop/preflight/copy config
- Usage Summary + Usage History (filtre + export)
- Dashboard: KPI/trend/breakdown/alerts/recent/top-expensive
- Persona Lite + Optimizations + Interceptors runtime etkisi
- Settings persistence/validation

### 2.3 Teknik Disiplin
- Evidence-first gate yaklasimi
- SSOT tabanli karar/izleme
- Scope daraltma ve false DONE engelleme

## 3) Stratejik Hedef

Hedef iki ayakli:
1) Kisa vade: stabil ve guvenilir release cikisi
2) Orta vade: domain-agnostic execution-fabric donusumu icin kontrollu zemin

Ana ilke: "Hemen full refactor" degil, "phase-gated migration".

## 4) Release'e Kadar Teknik Evreler (Uctan Uca Plan)

## Evre R0 - Karar Kilitleme (Hemen)
Amac: kapsam/genisleme tartismasini kapatmak, tek takip modeline gecmek.
Ciktilar:
- Master feature list kilidi
- Decision Packet v1 (contract/hook/gate taslagi)
- Release scope freeze kurali

Gate:
- Her feature tek sinifa mapli (RELEASE_NOW / MIGRATION_READY / FREEZE / POST_MIGRATION)

## Evre R1 - Release Kritik Tamamlama
Amac: kullanici tarafinda release kalitesini etkileyen dar aciklari kapatmak.
Odak:
- Onboarding / error recovery / destructive confirmation / update/rollback netligi
- Cost transparency minimum seti (Actual/Estimated/Unknown gorunurlugu)
- Legal/Compliance Minimum Pack (privacy notice, retention/deletion policy, telemetry disclosure, disclaimer)
- User Documentation Pack (user guide, known issues, feature wiki + yardim akis metinleri)
- P5.14C carry-forward netlestirme

Gate:
- Kritik akislarda NARROW/BLOCKER kalmamalı
- UI static checks + manual runtime reconfirm tamam
- Legal/Compliance minimum dokumanlari yayin-hazir
- User dokumantasyon paketi yayin-hazir ve ekranlarla tutarli

## Evre R2 - Vault Basic Denemesi (v1.0 aday)
Amac: market positioning gucunu arttirmak (privacy/local-first) ama onumuzu tikamamak.
Kural:
- 5 gun hard timebox
- Gun-3 cut rule: blocker/regresyon varsa Vault v1.1'e otomatik duser

Kapsam (dar):
- keyring ile credential store/list/select/delete
- Connections formunda "Vault'tan sec" entegrasyonu

Gate:
- No-regression on core flows
- Clear fallback plan (Vault off -> release devam)

## Evre R3 - Release Hardening
Amac: dagitim oncesi teknik guvenilirligi kilitlemek.
Odak:
- Packaging/update/rollback provasi
- Runtime stability pass
- Error handling/support hazirligi
- Security/hygiene hizli tarama

Gate:
- Go/No-Go tablosu tum kritik maddelerde PASS
- Rollback prova basarili

## Evre R4 - Release Adayi ve Kapanis
Amac: release kararini veri ile vermek.
Ciktilar:
- Final checklist
- Known issues
- Release notes/support runbook
- Son SSOT sync (yalniz gerekli minimal satirlar)

Gate:
- Release blocker yok
- Revalidate kalanlarin bilincli tasima/notlandirma karari net

## 5) Feature'larin Evrelere Dagilimi (Kilit Harita)

## RELEASE_NOW (v1.0 oncesi kapanacak)
- Mevcut calisan core yuzeyleri (F-001..F-025)
- Cost transparency minimum seti (F-031 + F-034)
- Kullanici guveni ve operasyon kalitesi etkileyen dar kritikler (onboarding/error/confirm/update)
- Legal/Compliance Minimum Pack (LC-MIN-01)
- User Documentation Pack (DOCS-MIN-01)
- P5.14C residual netlestirme

## MIGRATION_READY (v1.1 ve kontrollu genisleme)
- Cost metadata derinlesme (pricing_version/timestamp/confidence)
- Secili modul integrasyonlari (risk/etki sirali)
- Provider kapsami kontrollu genisleme
- Vault basic (eger v1.0'da cut olursa)
- Audit log (basic) paketi
- Performance optimization paketi (async + cache)

## FREEZE (release penceresinde dondur)
- Core boundary buyuten ama release'e direkt katkisi olmayan buyuk refactorlar
- Domain-agnostic implementasyonun agir fazlari

## POST_MIGRATION (v1.2+)
- Core envelope/hook/adapter kapsamli uygulama (F-038..F-047)
- Productization paketleri (F-048+)

## 6) Modul Entegrasyon Plani

## v1.0 (dar ve etkili set)
- loguru
- tenacity
- sentry-sdk
- litellm (cost baseline icin)
- keyring (Vault basic; yalniz timebox/cut-rule ile)

## v1.1 (stabilizasyon sonrasi)
- pydantic
- bleach
- python-dotenv
- cachetools
- audit log (basic)
- async/performance optimizasyon dilimi
- gerekli gorulurse: ek audit/security yardimci modulleri

## v1.2+ (mimari derinlesme)
- execution-fabric odakli katmanlar ve modul paketi

Entegrasyon ilkesi:
- Moduller toplu degil, etkisi kanitlanabilir dilimlerle alinacak.
- Her yeni modul icin: deger, risk, fallback, test-gate zorunlu.

## 7) Numeric Gate Seti (Operasyonel)

A) Stability Gate
- Kritik akis regresyon sayisi: 0 blocker
- Manual runtime reconfirm: kritik akislarda PASS

B) Quality Gate
- UI static check: PASS
- Dispatch/error contract bozulmasi: 0

C) Release Gate
- Packaging + rollback prova: PASS
- Known issues listesi: tamam

D) Scope Gate
- Release disi yeni feature ekleme: kapali (change control olmadan yok)
- Her yeni item once feature remap sinifina girecek

E) Documentation & Compliance Gate
- Legal/Compliance Minimum Pack maddeleri tamam
- User Guide + Known Issues + Feature Wiki paketi tamam

## 8) Riskler ve Koruma

R1 - Scope creep
- Koruma: feature remap kilidi + change control

R2 - Vault kaynakli takvim kaymasi
- Koruma: 5 gun timebox + gun-3 cut rule

R3 - Cost guvenilirligi algi riski
- Koruma: Actual/Estimated/Unknown etiketleri

R4 - SSOT ve uygulama gercegi ayrismasi
- Koruma: minimal ama surekli SSOT sync

R5 - Yetersiz legal/dokumantasyon kalkanı
- Koruma: LC-MIN-01 + DOCS-MIN-01 release gate'e bagli zorunlu paket

## 9) Calisma Sekli (Roller)

- Supervisor (burada): SSOT, gate, risk ve roadmap disiplini
- Builder: task-bounded implementasyon
- Kullanici: canli test geri bildirimi + oncelik karari

## 10) Karar Noktalari (Yakindaki)

K1: Vault v1.0 denemesi gun-3 gate'i geciyor mu?
K2: P5.14C residual alan release oncesi kapanir mi, bilincli tasima mi?
K3: v1.1 modul setinde hangi sira ile ilerlenir?

## 11) Kisa Uygulama Takvimi (Pragmatik)

- Hafta 1: R0 + R1 baslangic + Vault dilimi acilisi
- Hafta 2: R1 kapanis + R2 gate karari + R3 hazirlik
- Hafta 3: R3 hardening + R4 aday
- Hafta 4: R4 karar ve release

Not: Takvim, yeni blocker cikarsa R2 cut-rule ile korunur.

## 12) Final Yorum

Bu planin amaci ayni anda iki seyi basarmak:
1) release'i guvenli sekilde cikarmak,
2) domain-agnostic platformlasma hedefini teknik borca donusturmeden tasimak.

Bunun ana kosulu: scope disiplini + evidence-first gate + dar dilim implementasyon.
