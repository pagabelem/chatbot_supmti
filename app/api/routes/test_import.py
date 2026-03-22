# test_import.py
try:
    from transformers import pipeline
    print("✅ transformers est importé avec succès!")
    print(f"📦 Version: {pipeline.__module__}")
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    
    # Vérifier le chemin Python
    import sys
    print("\n📁 Chemins Python:")
    for path in sys.path:
        print(f"  - {path}")