# tests/test_ocr_simple.py
import easyocr
import cv2
import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import re
import time

def initialize_ocr():
    """Initialise le lecteur OCR avec gestion d'erreurs"""
    print("🔄 Initialisation du lecteur OCR...")
    print("(Cela peut prendre quelques secondes au premier lancement)")
    
    try:
        # Tentative d'initialisation avec plusieurs combinaisons
        lang_combinations = [
            ['en', 'fr'],           # Anglais + Français
            ['en'],                  # Anglais seulement
            ['en', 'ar', 'fr'],      # Anglais + Arabe + Français
            ['en', 'ar']             # Anglais + Arabe
        ]
        
        reader = None
        for langs in lang_combinations:
            try:
                print(f"🔄 Essai avec {langs}...")
                reader = easyocr.Reader(langs, gpu=False)
                print(f"✅ Lecteur OCR prêt avec {langs} !")
                break
            except Exception as e:
                print(f"⚠️ Échec avec {langs}: {e}")
                continue
        
        if reader is None:
            raise Exception("Impossible d'initialiser l'OCR avec aucune combinaison de langues")
        
        return reader
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
        return None

def create_test_image():
    """Crée une image de test avec du texte"""
    test_image_path = 'tests/test_texte.png'
    
    if os.path.exists(test_image_path):
        print(f"📸 Image existante trouvée: {test_image_path}")
        return test_image_path
    
    print("📸 Création d'une image de test...")
    
    # Créer une image avec du texte
    img = Image.new('RGB', (800, 300), color='white')
    d = ImageDraw.Draw(img)
    
    # Essayer de charger une police, sinon utiliser la défaut
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    # Texte de test (multilingue)
    texts = [
        ("SUP MTI Meknès", (10, 10)),
        ("Intelligence Artificielle", (10, 40)),
        ("Note: 16.5/20", (10, 70)),
        ("Mathématiques: 14", (10, 100)),
        ("Français: 15", (10, 130)),
        ("Anglais: 17", (10, 160)),
        ("السلام عليكم", (10, 190)),  # Arabe
        ("Bienvenue à SUP MTI", (10, 220))
    ]
    
    for text, position in texts:
        d.text(position, text, fill='black', font=font)
    
    # Sauvegarder
    img.save(test_image_path)
    print(f"✅ Image de test créée: {test_image_path}")
    return test_image_path

def extract_grades(texts):
    """Extrait les notes potentielles du texte"""
    notes = []
    grade_patterns = [
        r'(\d+[.,]?\d*)\s*\/\s*20',  # 15/20
        r'note:?\s*(\d+[.,]?\d*)',    # note: 15
        r'(\d+[.,]?\d*)\s*\/\s*20?',  # 15/20 (variante)
    ]
    
    for text in texts:
        text_lower = text.lower()
        for pattern in grade_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                notes.append({
                    'text': text,
                    'grade': match.group(1) if match.groups() else match.group(0)
                })
                break
    
    return notes

def main():
    """Fonction principale"""
    start_time = time.time()
    
    # 1. Initialiser l'OCR
    reader = initialize_ocr()
    if not reader:
        return
    
    # 2. Créer ou récupérer l'image de test
    test_image_path = create_test_image()
    
    # 3. Analyser l'image
    print(f"\n🔍 Analyse de l'image: {test_image_path}")
    try:
        result = reader.readtext(
            test_image_path,
            paragraph=False,  # Ne pas fusionner les lignes
            contrast_ths=0.1,  # Seuil de contraste
            adjust_contrast=0.5,  # Ajustement du contraste
            text_threshold=0.7  # Seuil de confiance
        )
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")
        return
    
    # 4. Afficher les résultats
    print(f"\n📝 Texte détecté ({len(result)} éléments):")
    print("=" * 60)
    
    all_texts = []
    for i, (bbox, text, confidence) in enumerate(result):
        all_texts.append(text)
        print(f"{i+1}. 📄 Texte: '{text}'")
        print(f"   ✓ Confiance: {confidence:.2%}")
        print(f"   📍 Position: {bbox}")
        print()
    
    # 5. Chercher les notes
    print("🔎 Recherche de notes dans le texte...")
    notes = extract_grades(all_texts)
    
    if notes:
        print("📊 Notes trouvées:")
        for note in notes:
            print(f"   • {note['text']} → valeur: {note['grade']}")
    else:
        print("ℹ️ Aucune note détectée")
    
    # 6. Statistiques
    elapsed_time = time.time() - start_time
    print(f"\n✅ Test terminé en {elapsed_time:.2f} secondes!")
    print(f"📊 Statistiques:")
    print(f"   - Total éléments détectés: {len(result)}")
    print(f"   - Notes trouvées: {len(notes)}")
    print(f"   - Confiance moyenne: {sum(c for _,_,c in result)/len(result):.2%}")

if __name__ == "__main__":
    main()