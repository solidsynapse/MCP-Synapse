# Maliyet Modulu Fizibilite ve Uygulanabilirlik On Degerlendirme

## 1) Amac
Bu dokuman, MCP Synapse icin "tutarli ve guvenilir maliyet tahmini" hedefinin teknik olarak nasil gerceklestirilebilecegini on degerlendirme seviyesinde netlestirir.
Kapsam bilerek dar tutulmustur: nihai mimari karari degil, karar oncesi uygulanabilirlik resmi cizilir.

## 2) Mevcut Durum Ozeti (Current Truth)
- Maliyet verisi provider bazinda esit kalitede degil.
- Vertex tarafinda maliyet bilgisi uretiliyor; diger providerlarda cost_usd alani tutarli degil / bos kalabiliyor.
- Dashboard ve usage yuzeyleri maliyet goruntuleyebiliyor; ancak "estimate vs actual" ayrimi her kayitta acik ve standardize degil.
- Budget guard akisinda maliyet verisinin kaynagi (gercek/tahmin) ayrimi operasyonel karar kalitesini dogrudan etkiliyor.

## 3) Problem Taniminin Cekirdegi
Tek engel "hesap formulu" degil; asil konu su:
1. Provider fiyatlari degisken (zaman/bolge/model revizyonu etkisi)
2. Token olcumu providerlar arasinda farkli
3. Bazi cevaplarda authoritative maliyet donmuyor
4. Kullaniciya tek bir "cost" sayisi gosterip guven seviyesini saklamak karar hatasina neden oluyor

## 4) En Uygun Yapi (Onerilen)
Iki katmanli bir maliyet modeli:

### Katman A - Actual Provider Cost
Provider authoritative maliyet donuyorsa birincil kaynak budur.
- Kayit etiketi: `cost_source=ACTUAL_PROVIDER`
- Guven seviyesi: yuksek
- Bu veri raporlama ve alarm tarafinda en oncelikli kabul edilir.

### Katman B - Estimated Registry Cost
Actual yoksa standart fiyat registry + token sayimi ile tahmin hesaplanir.
- Kayit etiketi: `cost_source=ESTIMATED_REGISTRY`
- Ek alanlar:
  - `pricing_version`
  - `pricing_timestamp`
  - `estimation_confidence` (LOW/MEDIUM/HIGH)
- Guven seviyesi: orta veya dusuk (providera gore)

Bu modelle sistem "tek sayi verip belirsizligi gizlemek" yerine belirsizligi kontrollu sekilde tasir.

## 5) Neden Bu Yapi En Uygulanabilir?
- Mevcut sisteme buyuk refactor gerektirmez (minimal schema + hesaplama katmani)
- Yeni provider ekleme hizi korunur (provider-agnostic strateji bozulmaz)
- Maliyet kalitesi asamali olarak artirilir (big-bang zorunlulugu yok)
- UI/raporlar "actual vs estimate" farkini acik gosterebilir

## 6) Fizibilite Skoru (On Degerlendirme)
- Teknik fizibilite: Yuksek
- Operasyonel fizibilite: Yuksek
- Veri guvenilirligi riski: Orta (fiyat guncelligi ve token farklari)
- Teslimat karmasikligi: Orta-dusuk (dogru scope ile)

## 7) Minimum Uygulanabilir Kapsam (MVP)
Asama 1 (en dusuk risk):
1. Kayit modeline `cost_source` ekle
2. Estimate hesaplamada `pricing_version` + `pricing_timestamp` sakla
3. UI'da cost etiketini "Actual / Estimated / Unknown" olarak goster

Asama 2:
1. Alarm/policy ekranlarinda estimated veriye gore "confidence-aware" metin kullan
2. Raporlarda actual ve estimated toplamlari ayri kirilimla sun

Asama 3:
1. Provider bazli quality score
2. Repricing/snapshot stratejisi (geriye donuk tutarlilik icin)

## 8) Kritik Riskler ve Koruma Onlemleri
- Risk: Fiyat verisi eski kalir
  - Onlem: Surumlu fiyat snapshot modeli ve kontrollu guncelleme takvimi
- Risk: Estimated maliyet actual gibi algilanir
  - Onlem: UI'da acik etiket + tooltip + rapor dipnotu
- Risk: Provider token semantik farklari
  - Onlem: Provider bazli confidence seviyesi + test fixture seti

## 9) Bu Fazda Alinmasi Gereken Kararlar
1. Standart maliyet sozlesmesi (cost contract) zorunlu alanlari
2. Fiyat kaynagi surumleme modeli
3. "Unknown cost" durumunda UI/policy davranisi
4. Budget guard kararlarinda estimated verinin etkisi

## 10) Sonuc
Bu proje icin en dengeli yol, tek tip "kesin maliyet" iddiasi yerine iki katmanli ve izlenebilir bir maliyet modeli kurmaktir.
Bu yaklasim:
- Hizli uygulanir
- Mevcut mimariyla uyumludur
- Provider cesitliligine acik kalir
- Guvenilirligi zamanla arttirir

Bu dokuman bilerek on degerlendirme seviyesindedir. Sonraki adimda core moduler yapi ve feature eklemlenmesi bu maliyet kontrati etrafinda kesinlestirilmelidir.
