# test_ocr.py
import easyocr
import requests
from PIL import Image
from io import BytesIO

print("🔄 Chargement du modèle OCR...")
reader = easyocr.Reader(['fr', 'en'])  # Français et anglais
print("✅ Modèle OCR chargé !\n")

# Test avec une image de test (exemple de texte)
print("📸 Test avec une image simple...")

# Créer une image de test simple avec PIL
from PIL import Image, ImageDraw, ImageFont

img = Image.new('RGB', (400, 100), color='white')
d = ImageDraw.Draw(img)
d.text((10, 10), "SUP MTI Meknès", fill='black')
d.text((10, 40), "Intelligence Artificielle", fill='black')
d.text((10, 70), "Bienvenue !", fill='black')

# Sauvegarder l'image
img.save('test_ocr.png')
print("✅ Image de test créée: test_ocr.png")

# Lire le texte
print("\n🔍 Lecture du texte...")
result = reader.readtext('test_ocr.png')

print("📝 Texte détecté:")
for detection in result:
    print(f"   - {detection[1]} (confiance: {detection[2]:.2f})")