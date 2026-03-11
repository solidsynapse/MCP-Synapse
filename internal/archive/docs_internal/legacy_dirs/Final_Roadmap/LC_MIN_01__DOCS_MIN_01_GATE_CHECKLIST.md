# LC-MIN-01 + DOCS-MIN-01 Gate Checklist (Release-Now)

Durum: Supervisor gate checklist (task-bounded)
Amac: v1.0 scope'u bozmadan minimum legal/compliance kalkanini ve user-facing dokumantasyon paketini kapanis kriterleri ile netlestirmek.

## 1) Scope

### Scope IN
- LC-MIN-01 (Legal/Compliance Minimum Pack)
- DOCS-MIN-01 (User Documentation Pack)
- Sadece dokumantasyon ve release-readiness gate kaniti

### Scope OUT
- Kod refactor
- Runtime davranis degisikligi
- SSOT normlarini genisletme
- Mimari kapsam buyutme

## 2) Paket Bilesenleri

## LC-MIN-01
- Privacy Notice (minimum GDPR-temel)
- Data retention/deletion policy
- Telemetry/third-party disclosure (var/yok acik)
- Terms/Disclaimer (product boundary + sorumluluk siniri)
- Security contact / incident reporting metni

## DOCS-MIN-01
- User Guide (ilk kullanim + temel akislar)
- Known Issues (mevcut bilinen sinirlar + workaround)
- Feature Wiki (mevcut ana feature setin sade anlatimi)
- Troubleshooting (baglanti, preflight, usage/export, dashboard)

## 3) Minimum Acceptance (kapanis kriteri)

### A) Completeness Gate
- LC-MIN-01 bilesenlerinin tamami mevcut
- DOCS-MIN-01 bilesenlerinin tamami mevcut

### B) Consistency Gate
- Dokumantasyon metinleri mevcut urun davranisiyla celismiyor
- Budget semantics D-031 ile uyumlu (monitor-only)
- Cost dili Actual/Estimated/Unknown ayrimini bozmayacak sekilde yazili

### C) Operability Gate
- Kullanici, uygulamayi ilk acista temel akislari dokumandan takip edebiliyor
- Known issues listesi release notlariyla uyumlu
- Critical support route (sorun bildirimi) metni net

### D) Release Gate
- LC-MIN-01 ve DOCS-MIN-01 release blocker olarak PASS
- Acik kalan maddeler varsa bilincli REVALIDATE notu ile tasinmis

## 4) Evidence Beklentisi

Her alt dilim icin minimum:
- commands_ran.txt
- anchor_proofs.txt
- ssot_core.sha256.before.txt
- ssot_core.sha256.after.txt
- summary.txt

Opsiyonel:
- docs_diff.txt
- checklist_trace.txt

## 5) Verdict Kurali

- PASS:
  - Tum acceptance maddeleri kapanmis
  - D-031 ve mevcut current truth ile celiski yok

- REVALIDATE:
  - Icerik var ama davranis uyumu/ifadeler net degil
  - En az bir madde yeniden dogrulama gerektiriyor

- BLOCKER:
  - Legal minimum maddelerden biri eksik
  - Kullanici dokumani release temel akislarini tasimiyor
  - SSOT normlariyla dogrudan celiski var

## 6) Uygulama Sirasi (dar)
1. LC-MIN-01 draft
2. DOCS-MIN-01 draft
3. Supervisor micro gate check
4. REVALIDATE varsa tek tur wording fix
5. Final PASS/REVALIDATE karari

## 7) Notlar
- Bu checklist release hizini yavaslatmak icin degil, release riskini dusurmek icin vardir.
- Hukuki metinler teknik baglamla uyumlu ama yalniz hukuki danisman yerine gecmez.
