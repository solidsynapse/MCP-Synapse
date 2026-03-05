# Teknik Guvenilirlik Temelli Roadmap On Raporu

Durum: Teorik ama kanit-temelli on degerlendirme.
Amac: 4 temel dokuman + SSOT pusulasi ile uygulanabilir roadmap catisini netlestirmek.
Not: Bu belge implementasyon karari degildir; karar-oncesi cercevedir.

## 1) Yurutucu Sonuc
Bu donusum (domain-agnostic execution-fabric hedefi), MCP Synapse icin yuksek kaldirac potansiyeli tasiyor.
Ancak dogru siralama zorunlu:
1) release istikrari korunmali,
2) phase-gated migration modeli uygulanmali,
3) cost module kontrati migrationin erken fazinda sabitlenmeli.

On karar:
- "Tam donusum simdi" = yuksek takvim/regresyon riski
- "Kanitli hibrit yol" = en uygulanabilir secenek

## 2) Kanit Temeli (Belge Blogu)
Bu rapor asagidaki 4 ana dayanak + SSOT pusulasini birlikte kullanir:
1. Hedef mimari: docs/domain-agnostic-fizibilite/Execution_Fabric_Fizibilite_On_Degerlendirme.md
2. Kritik feature: docs/maliyet_modulu_calisma/Maliyet_Modulu_Fizibilite_On_Degerlendirme.md
3. Strateji gercekligi: docs/MASTERPLAN_CAPABILITY_TRUTH_AND_STRATEGY.md
4. Mevcut durum: docs/CurrentState_WorksLeft.md
5. Normatif pusula: DECISIONS + STATUS + TASKS + UI_STYLE_GUIDE

## 3) Tumevarim Modeli (Neyi birlestiriyoruz?)
Roadmap uretimi su 4 eksenin kesisiminden yapilir:
- E1: Hedef mimari (nereye gidiyoruz)
- E2: Mevcut capability truth (bugun ne calisiyor)
- E3: Kritik aciklar ve teknik borc (ne donusmeli)
- E4: SSOT gate/karar disiplini (ne zaman PASS sayilir)

Bu 4 eksen birlikte kullanildiginda kapsam kaymasi azalir ve "false DONE" riski duser.

## 4) Is Buyuklugu ve Takvim Bandi (teorik tahmin)
A) On fizibilite + karar paketi: 1-2 hafta
B) Dar pilot (compatibility + 1-2 hook): 2-4 hafta
C) Fazli tam donusum: 8-12 engineer-week (tek akis takvimde 10-16+ hafta)

Okuma:
- Kisa vadede en rasyonel yol A + B
- C sadece gate kriterleri olgunlasinca baslatilmali

## 5) Tutarlı Risk Analizi
### 5.1 Stratejik risk
- R1: MVP/Release stabilitesini bozacak erken full refactor
- R2: Release sonrasi migrationin ertelenip borcun katlanmasi

### 5.2 Teknik risk
- R3: Core contract kirilmasi (payload/backward uyumu)
- R4: Hook determinism boslugu (sync/async, timeout, cancel)
- R5: Observability migration sapmasi
- R6: Policy wiringin monitor-only -> enforce gecisinde regresyon

### 5.3 Operasyonel risk
- R7: Dual-path test maliyeti
- R8: Sprint bazli karar dagilmasi (owner/gate belirsizligi)

### 5.4 Azaltma modeli
- Compatibility-first
- Phase gate + entry/exit evidence
- Monitor-only baslangic
- Kill-switch + rollback provasi
- KPI ile gate karar

## 6) Pratik Kaldirac (Gercekte ne kazandirir?)
1) Feature delivery hizi:
- Core'a dogrudan mudahale yerine hook/plugin ekleme hizi artar.

2) Domain tasinabilirligi:
- LLM-spesifik kontratlardan domain-neutral execution kontratina gecis, yeni dikeyleri hizlandirir.

3) Urunlesme:
- Core + module + adapter modeli ile paketlenebilir urun cizgileri dogar.

4) Governance:
- Policy etkileri lifecycle uzerinden daha olculebilir ve denetlenebilir olur.

Sinir:
- Bu donusum tek basina PMF yaratmaz; siralama yanlis olursa fayda yerine yavaslama getirir.

## 7) Ilk Release Yapisi ve Bekleyen Feature'lar
### 7.1 Ilk release yapisi (onerilen)
- Core runtime stabil; minimum boundary degisimi
- Policy agirlikla monitor-only
- UI thin-shell yonelimli ama zorlamasiz
- Mevcut contractlarda compatibility korunur

### 7.2 Bekleyen feature'larin siniflandirma modeli
Her item su 4 siniftan birine zorlanir:
1. RELEASE_NOW: mevcut release penceresinde gerekli
2. MIGRATION_READY: donusum pilotunda guvenli tasinabilir
3. FREEZE: su an core boundary buyutur, ertelenir
4. POST_MIGRATION: hedef mimari oturmadan alinmaz

Bu model, backlogu roadmape teknik tutarlilikla baglar.

## 8) Maliyet Modulu ile Birlesik Okuma
Maliyet modulu, execution-fabric donusumunun erken kritik parcasi olmali.
Neden:
- cost_source (actual/estimated/unknown) ayrimi governance ve policy kararlarini dogrudan etkiler
- provider-agnostic iddiayi olculebilir hale getirir
- budget ve dashboard karar kalitesini artirir

Oneri:
- cost contract v0, core contract v0 ile ayni karar paketinde sabitlensin.

## 9) Onerilen Go/No-Go Cercevesi
GO kosullari:
1) Core contract v0 taslak onayi
2) Hook semantics v0 netligi
3) Cost contract v0 netligi
4) Compatibility + rollback plani yazili
5) Faz KPI ve gate ownerlari tanimli

NO-GO tetikleyicileri:
1) Release stabilitesini bozacak kapsam genislemesi
2) Determinism testlerinin guvensiz kalmasi
3) Policy enforce gecis kriterlerinin belirsizligi

## 10) Roadmap Uretimi Icin Bir Sonraki Cikti (hazirlik)
Bu rapordan sonra tek bir "Roadmap Decision Packet" uretilebilir:
- Stream A: Release stabilization ve quality gates
- Stream B: Execution-fabric migration (A-F fazlari)
- Stream C: Cost module contract + rollout
- Stream D: Feature backlog remap (4 sinif modeli)

Her stream icin:
- giris/ cikis gate
- owner
- KPI
- risk ve rollback

## 11) Net Sonuc
Evet, bu belge blogu ile "gercek resim" cizilebilir.
Evet, bu atilim degerli olabilir.
Ama kosul su: release istikrari + evidence-first phase-gated migration disiplini.

Bu cerceveyle ilerlenirse hem bugunku urun ivmesi korunur hem de domain-agnostic platformlasma teknik olarak yonetilebilir bir plana donusur.
