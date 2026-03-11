# test_openai_stt.py
import os
from dotenv import load_dotenv
import openai

# Charge les variables d'environnement
load_dotenv()

def test_openai_connection():
    """Test simple de connexion à OpenAI"""
    
    print("=" * 50)
    print("🔍 TEST DE CONNEXION OPENAI")
    print("=" * 50)
    
    # Vérifier la clé API
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ ERREUR: OPENAI_API_KEY non trouvée dans .env")
        print("\nVérifie que ton fichier .env contient:")
        print("OPENAI_API_KEY=ta_cle_api_ici")
        return False
    
    # Afficher un aperçu de la clé (sécurisé)
    print(f"✅ Clé API trouvée: {api_key[:8]}...{api_key[-4:]}")
    
    try:
        # Initialiser le client
        client = openai.OpenAI(api_key=api_key)
        
        # Tester la connexion en listant les modèles
        print("\n🔄 Test de connexion à OpenAI...")
        models = client.models.list()
        
        print(f"✅ Connexion réussie!")
        print(f"📊 Nombre de modèles disponibles: {len(models.data)}")
        
        # Afficher quelques modèles disponibles
        print("\n📋 Modèles disponibles (aperçu):")
        for model in models.data[:5]:
            print(f"  - {model.id}")
        
        # Test spécifique pour Whisper
        print("\n🎤 Vérification du modèle Whisper...")
        whisper_available = any("whisper" in model.id for model in models.data)
        
        if whisper_available:
            print("✅ Modèle Whisper disponible pour la transcription vocale")
        else:
            print("⚠️ Modèle Whisper non trouvé, vérifie tes permissions")
        
        return True
        
    except openai.AuthenticationError:
        print("❌ ERREUR: Clé API invalide")
        return False
    except openai.RateLimitError:
        print("❌ ERREUR: Quota dépassé (Rate limit)")
        return False
    except Exception as e:
        print(f"❌ ERREUR inattendue: {type(e).__name__}")
        print(f"Détail: {e}")
        return False

if __name__ == "__main__":
    success = test_openai_connection()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ TEST RÉUSSI - OpenAI est prêt à l'emploi!")
    else:
        print("❌ TEST ÉCHOUÉ - Vérifie ta configuration")
    print("=" * 50)