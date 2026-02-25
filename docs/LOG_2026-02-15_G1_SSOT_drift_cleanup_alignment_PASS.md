# LOG — 2026-02-15 — G1/SSOT drift cleanup + requirements & USER_GUIDE alignment (PASS)

**Phase:** Stabilization closeout → SSOT drift cleanup + controlled artefacts alignment  
**Scope boundary:** Stage 1 (%10) rollout gate’lerine geçilmedi (bilinçli olarak ertelendi).  
**Actors:** Supervisor (ChatGPT), Verifier (ChatGPT), Debugger (ad-hoc / IDE agent)

---

## 1) SSOT drift cleanup — PASS

### Problem
- TASKS checkbox drift (done olduğu halde [ ] kalmış).
- STATUS risk/next-action drift (V1 activation unclear / collect evidence).
- DECISIONS D-005 context drift (“no call-sites exist” artık yanlış).

### Changes applied
- docs/TASKS.md
  - T0.1 / T0.2 / T0.4: [ ] → [x]
  - flet pin drift: flet==0.21.2 → flet==0.80.5
- docs/STATUS.md
  - “V1 activation unclear …” kaldırıldı / drift cleanup risk maddesi ile değiştirildi
  - “Collect line-number evidence …” kaldırıldı / drift cleanup maddesi ile değiştirildi
  - Unknowns yalnızca “V1 used to work but not now” kanıt ihtiyacına indirildi
  - Evidence Index pipeline-v1 path archive’a hizalandı
- docs/DECISIONS.md
  - D-005 Context: “no call-sites exist” → “call-site exists as of T0.8 …”
  - wrap kaynaklı durum line-based patch ile kesin düzeltildi

### Evidence (Verifier outputs)
- Drift negatif aramaları (Select-String) temizlendi.
- D-005 context pozitif kanıtı: “call-site exists as of T0.8 …” satırı görüldü.

---

## 2) requirements.txt encoding + pins — PASS (controlled artefact)

### Problem
- requirements.txt BOM (EF BB BF) ile başlıyordu.

### Changes applied
- BOM kaldırıldı, UTF-8 no BOM normalize edildi.

### Evidence
- BOM tespiti: EF BB BF
- BOM sonrası: BOM yok (dosya artık EF BB BF ile başlamıyor)
- Pin kanıtı:
  - flet==0.80.5
  - pyperclip==1.11.0

---

## 3) USER_GUIDE build instructions SSOT alignment — PASS (controlled artefact)

### Problem
- USER_GUIDE build bölümü drift taşıyordu; SSOT’a bağlanmalıydı.

### Changes applied
- “## Building a Windows Executable” bölümü SSOT’a referans verecek şekilde rewrite edildi:
  - venv create/activate
  - pip install -r requirements.txt
  - flet pack …
  - expected output: dist\MCP Router.exe
  - “Source of truth: docs/STATUS.md …” notu

### Evidence
- USER_GUIDE içinde SSOT referansı ve komut satırları Select-String ile görüldü.

---

## 4) SSOT policy clarification — PASS

### Change applied
- docs/DECISIONS.md içine D-006 eklendi:
  - SSOT seti 5 dosyadır.
  - requirements.txt ve USER_GUIDE.md SSOT değildir; “controlled artefacts” olarak SSOT gate’leriyle yönetilir.

### Evidence
- DECISIONS.md içinde D-006 satırları Select-String ile görüldü.

---

## Roadmap (agreed)
- G1 drift cleanup ✅ (bitti)
- T0.3 repro + log capture
- Unknowns kapanır → STATUS temiz
- T1.x deterministic command hardening
- Controlled Rollout Stage 1 (%10)
- TRAE IDE agent hardening + sync
- Builder SOP stabilize