# Mini Fizibilite Sprint Charter (7-10 Gun)

Durum: Karar-oncesi dokumantasyon sprinti (kod implementasyonu degil)
Amaç: Roadmap ve Decision Packet'i uygulamaya alinabilir seviyeye getirmek.

## 1) Sprint Ciktisi (zorunlu)
1. Decision Packet v1
2. Core Contract v0 (alan + compatibility + versioning)
3. Hook Semantics v0 (order, timeout, cancellation, fail-open/fail-close)
4. Feature Remap Tablosu (RELEASE_NOW / MIGRATION_READY / FREEZE / POST_MIGRATION)
5. Numeric Gate Seti (Go/No-Go esikleri + rollback kurallari)

## 2) Kapsam
### Scope IN
- Sadece dokumantasyon, karar modelleme, gate tanimi.
- SSOT pusulasi ile uyumlu karar celvesi.
- Maliyet modulu ve provider stratejisinin MVP etkisi.

### Scope OUT
- Kod refactor/implementasyon.
- Runtime davranisi degistirecek patchler.
- SSOT normlarini keyfi genisletme.

## 3) Is Paketi Takvimi
- Gun 1-2: Core Contract v0
- Gun 3-4: Hook Semantics v0
- Gun 5-6: Feature Remap + Maliyet/Provider karar matrisleri
- Gun 7: Numeric gates + rollback policy
- Gun 8-10 (buffer): tutarlilik kontrolu + Decision Packet v1 kilidi

## 4) Karar Kilitleri (Sprint sonunda kapatilacak)
- K1: MVP cost davranisi nedir? (Actual/Estimated/Unknown etiketi zorunlulugu)
- K2: MVP provider kapsaminda minimum hedef nedir? (Vertex-only vs en az 1 ek provider)
- K3: Budget davranisi ne olacak? (D-031 uyumlu monitor-only kilidi)
- K4: Feature freeze siniri nasil uygulanacak?

## 5) Basari Kriteri
- Decision Packet v1 ile tek toplantida Go/No-Go verilebilir olmali.
- Her kritik karar icin trade-off + risk + gate eşiği yazili olmali.
- Roadmap ciktisi owner/takvim/gate seviyesinde uygulanabilir olmali.
