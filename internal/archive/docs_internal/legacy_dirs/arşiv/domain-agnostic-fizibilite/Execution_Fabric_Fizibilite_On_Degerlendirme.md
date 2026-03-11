# Execution Fabric Donusumu - On Fizibilite ve Uygulanabilirlik Degerlendirmesi

## 1) Yonetici Ozeti
Bu donusum, dogru siralama ile ilerlenirse MCP Synapse icin yuksek kaldiracli bir atilim olabilir.
Ancak bu adim, "simdi tam refaktor" olarak alinmamalidir.
En dogru yol: ilk release yapisini koruyup, release sonrasi fazli migration ve net gate modeli ile ilerlemek.

Kisa sonuc:
- Deger potansiyeli: yuksek
- Uygulama riski: orta-yuksek
- Simdi full donusum: onerilmez
- On fizibilite calismasi: kesinlikle degerli

## 2) Problem ve Firsat
Bugunku yapi provider-agnostic sinirina yakin, ama domain-agnostic execution-fabric seviyesinde degil.
Bu nedenle yeni modul/feature eklemede teknik borc birikiyor ve policy/wiring tarafi hizla karmasiklasabiliyor.

Execution-fabric hedefi ile:
- Core daha stabil ve daha az bagimli hale gelir
- Feature'lar plugin/hook modeliyle eklenebilir
- UI shell daha ince kalir, domain kararini core/moduller tasir
- Farkli domainlere uyarlama suresi haftalar seviyesine inebilir

## 3) Donusum Neden Gerekli Olabilir?
Donusumun gerekli olup olmadigi hedef ufka bagli:

### 3.1 Kisa ufuk (3-6 ay)
Hedef sadece mevcut urunun stabil calismasi ve artisli iyilestirmeyse tam donusum zorunlu degildir.

### 3.2 Orta/uzun ufuk (6-24 ay)
Hedef coklu domain, coklu module seti ve hizli uyarlama ise bu donusum stratejik olarak gereklidir.
Aksi halde her yeni capability core'u kirarak buyur.

## 4) Teorik Is Buyuklugu (Takvim ve Efor)
Not: Asagidaki tahminler teoriktir; uygulama oncesi planlama araligidir.

### Senaryo A - On Fizibilite + Karar Paketi
- Sure: 1-2 hafta
- Cikti: contract v0, hook lifecycle v0, migration gate v0, risk modeli
- Risk: dusuk

### Senaryo B - Dar Pilot (non-breaking)
- Sure: 2-4 hafta
- Cikti: compatibility envelope + 1-2 hook + monitor-only policy baglantisi
- Risk: orta

### Senaryo C - Fazli Tam Donusum
- Sure: 8-12 engineer-week (tek akis takvimde genelde 10-16+ hafta)
- Cikti: core/module/adapter siniri, plugin registry, gozlem normalizasyonu
- Risk: orta-yuksek

## 5) Tutarli Risk Analizi

### 5.1 Stratejik riskler
1. Yanlis siralama riski: release oncesi agresif refaktor takvimi kirar.
2. Erteleme riski: release sonrasi donusum disiplinsiz kalirsa teknik borc daha da sertlesir.

### 5.2 Teknik riskler
1. Contract kirilmasi: mevcut payload beklentileri bozulabilir.
2. Hook determinism riski: sync/async, timeout, cancellation net degilse beklenmeyen davranislar olusur.
3. Gozlem sapmasi: metrik semasi migration sirasinda kayabilir.
4. Policy wiring riski: monitor-only/enforce gecisleri kontrolsuz yapilirsa regresyon olur.

### 5.3 Operasyonel riskler
1. Test yuku artisi: dual-path donemde regression maliyeti yukselir.
2. Karar yorgunlugu: core prensipleri netlesmeden sprintler dagilir.

### 5.4 Risk azaltma yaklasimi
- Compatibility-first
- Phase gate + entry/exit kriterleri
- Monitor-only baslangic
- Kill-switch ve rollback provasi
- Her faz sonunda olculebilir kanitli karar

## 6) Pratik Kaldirac (Gercek Hayatta Neyi Degistirir?)

### 6.1 Beklenen fayda alanlari
1. Feature delivery hizi:
- Bugun: yeni policy/feature core'a temasla gelir
- Sonra: plugin/hook uzerinden kontrollu ekleme

2. Domain tasinabilirligi:
- Bugun: LLM odakli sozlesmeler yeniden kullanimi sinirliyor
- Sonra: execution contract domain-neutral kalir

3. Urun ailesi olusturma:
- Bugun: tek urun genisleme modeli
- Sonra: core + module + adapter ile paketlenebilir urun hatlari

4. Governance ve audit:
- Bugun: daginik policy etkileri
- Sonra: belirgin lifecycle, daha guvenilir denetim izi

### 6.2 Beklenen sinirlar
- Bu donusum tek basina urun-market-fit yaratmaz.
- Yanlis sequencing olursa hiz kazandirmak yerine yavaslatir.
- Ucuz bir is degil; ama kontrollu ilerlerse yatirim geri donusu yuksek olabilir.

## 7) Ilk Release Yapisi Icin Onerilen Cerceve
Donusum hedefi, ilk release'in istikrarini bozmamali.

### 7.1 Ilk release yapisi
- Core runtime: stabil, minimum degisim
- Policy davranislari: monitor-only agirlikli
- UI: thin render shell ilkesine yakin ama zorlamasiz
- Compatibility: mevcut payload yuzeylerini koru

### 7.2 Release sonrasi hemen baslayacak donusum
- Faz A: core contract v0 + error taxonomy v0
- Faz B: compatibility envelope
- Faz C: hook chain no-op defaults
- Faz D+: policy modulleri asamali tasima

## 8) Henuz Eklemlenmeyen Feature'lar Ne Olacak?
Ayrim net olmalidir:

1. Keep for release:
- release-ready ve stabil yuzeyler

2. Freeze (donusum sonrasina):
- core boundary'yi buyuten feature talepleri

3. Pilot candidate:
- donusumu test etmek icin dusuk riskli 1-2 capability

4. Backlog/roadmap:
- domain adapter gerektiren ama acil olmayan setler

Bu ayrim olmadan donusum sureci her sprintte kapsam kaymasina girer.

## 9) Go / No-Go Cercevesi

### Go icin minimum kosullar
1. Contract v0 taslagi ekipce anlasilmis
2. Hook lifecycle semantigi (sync/async, timeout, cancel) net
3. Compatibility ve rollback plani yazili
4. Gate KPI'lari olculebilir

### No-Go tetikleyicileri
1. Release stabilitesini bozan belirsiz scope buyumesi
2. Determinism testlerinin guvensiz kalmasi
3. Migrationin owner'larinin net olmamasi

## 10) Onerilen Sonraki Adim (Uygulama karari almadan)
1. 7-10 gunluk mini fizibilite sprinti
2. Cikti: Architecture Decision Packet v0
   - Core contract v0
   - Hook semantics v0
   - Migration gates v0
   - Risk register v0
3. Bu paketle birlikte son Go/No-Go karari

## 11) Net Karar Notu
Bu calisma kesinlikle yapmaya deger.
Ama bu bir "hemen tum sistemi kirip yeniden kur" karari degil.
Dogru karar modeli: once release istikrari, hemen ardindan kanitli fazli donusum.

Bu yaklasimla hem bugunku urun ivmesi korunur hem de uzun vadeli platform kaldiraci gercekten kurulabilir.
