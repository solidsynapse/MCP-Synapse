import os
import vertexai
from vertexai.preview.generative_models import GenerativeModel
from google.api_core.exceptions import PermissionDenied, NotFound, ServiceUnavailable

# AYARLAR
PROJECT_ID = "tensile-cogency-483219-q5"
CREDENTIALS_FILE = "key.json"
LOCATIONS_TO_TRY = ["us-central1", "us-east1", "us-west1", "europe-west1"] 
# (Eğer us-central1 çalışmazsa diğerlerini de denesin diye listeyi genişlettim)

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS_FILE

print(f"🕵️‍♂️ DETAYLI ARIZA TESPİTİ BAŞLIYOR...")
print(f"📂 Kimlik Dosyası: {CREDENTIALS_FILE}")

for location in LOCATIONS_TO_TRY:
    print(f"\n🌍 BÖLGE DENENİYOR: {location}")
    print("-" * 30)
    
    try:
        vertexai.init(project=PROJECT_ID, location=location)
        model = GenerativeModel("gemini-1.5-flash-001")
        
        print(f"   👉 Model çağırılıyor (gemini-1.5-flash-001)...")
        response = model.generate_content("Hello")
        
        print(f"   ✅ BAŞARILI! Cevap alındı: {response.text}")
        print(f"   🎉 ÇALIŞAN KONFİGÜRASYON:")
        print(f"      Location: {location}")
        print(f"      Model: gemini-1.5-flash-001")
        break # Çalışanı bulduk, bitir.
        
    except PermissionDenied as e:
        print(f"   🚨 YETKİ HATASI (403): API aktif değil veya servis hesabı yetkisiz.")
        print(f"   💡 İPUCU: Google Cloud Console'da 'Vertex AI API' etkinleştirildi mi?")
        print(f"   🔍 Detay: {e}")
        break # Yetki yoksa diğer bölgeleri denemenin anlamı yok.
        
    except NotFound as e:
        print(f"   ❌ BULUNAMADI (404): Bu bölgede bu model yok veya proje hatalı.")
        
    except Exception as e:
        print(f"   ⚠️ BEKLENMEYEN HATA: {type(e).__name__}")
        print(f"   📝 Mesaj: {e}")

print("\n🏁 Test Tamamlandı.")