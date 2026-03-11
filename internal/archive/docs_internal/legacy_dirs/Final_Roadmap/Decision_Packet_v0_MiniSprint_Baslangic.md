# Decision Packet v0 (Mini Sprint Baslangic)

Durum: Taslak v0 (Sprint sonunda v1'e kilitlenecek)

## 1) Problem Tanimı
MCP Synapse mevcutta calisan provider-agnostic zemine sahip; ancak domain-agnostic execution-fabric seviyesinde degil.
Sonuc: yeni feature/modul eklemelerinde core temas artiyor, teknik borc birikiyor, roadmap kararlari zorlasiyor.

## 2) Karar Hedefi
Asagidaki sorulara tek bir paketle karar verilebilir hale gelmek:
1. Donusum simdi mi, fazli mi?
2. MVP kapsaminda maliyet ve provider stratejisi ne olacak?
3. Hangi backlog kalemleri release'e girer, hangileri freeze edilir?

## 3) Normatif Kisitlar (SSOT)
- D-004: Usage/KPI contract deterministic kalmali.
- D-031: Budget guard monitor-only kilidi devam eder; enforce defer.
- STATUS/TASKS current truth ile celismeyen karar modeli kullanilacak.

## 4) Opsiyonlar
### Opsiyon A - Simdi Full Donusum
- Artı: uzun vadeli temiz mimariye hizli gecis
- Eksi: takvim/regresyon riski yuksek
- Ilk karar: Su an icin onerilmez

### Opsiyon B - Hibrit (onerilen)
- Release stabilitesi korunur
- Hemen sonrasinda phase-gated migration baslar
- Maliyet modulu ve provider stratejisi kontrat seviyesinde erkenden sabitlenir

## 5) MVP Kapsam Kararlari (taslak)
### C1 - Maliyet Davranisi
- Minimum zorunlu: Actual/Estimated/Unknown ayrimi
- Budget ve dashboard metinleri cost_source farkini yansitmali

### C2 - Provider Kapsami
- Iki yol:
  1) Vertex-only controlled MVP
  2) Vertex + en az 1 ek provider (dar scope)
- Nihai secim, sprint sonunda risk/takvim tablosuna gore kilitlenecek

### C3 - Budget Davranisi
- D-031 uyumlu monitor-only kilidi korunur
- Enforce davranisi bu sprintte karar metnine not edilir, implement edilmez

### C4 - Release Legal/Docs Kilidi
- Legal/Compliance Minimum Pack (privacy notice, retention/deletion, telemetry disclosure, disclaimer) v1.0 scope'una dahil
- User Documentation Pack (user guide + known issues + feature wiki) v1.0 scope'una dahil

## 6) Backlog Siniflandirma Modeli
Her item bu siniflardan birine zorunlu maplenecek:
- RELEASE_NOW
- MIGRATION_READY
- FREEZE
- POST_MIGRATION

## 7) Go/No-Go Gate Taslagi
### GO
1. Core Contract v0 onayi
2. Hook Semantics v0 onayi
3. Cost Contract v0 onayi
4. Numeric gate seti netligi
5. Owner ve takvim baginin kurulmasi

### NO-GO
1. Release stabilitesini bozacak kapsam kaymasi
2. Determinism test modeli belirsizligi
3. Migration owner ve rollback kurgusunun belirsiz kalmasi

## 8) Sprint Sonu Beklenen Nihai Cikti
Decision Packet v1:
- Karar metni (tek-seferde karar verilebilir)
- Roadmap streamleri (Release / Migration / Cost / Feature remap)
- Her stream icin gate, owner, KPI, rollback
