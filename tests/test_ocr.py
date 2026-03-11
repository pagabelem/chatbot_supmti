import easyocr
import cv2

# Initialiser le lecteur OCR
reader = easyocr.Reader(['fr', 'en'])  # Français et anglais

# Lire l'image (mets une vraie image dans le dossier tests/)
resultat = reader.readtext('bulletin.jpg')

# Afficher le texte trouvé
for (bbox, texte, confiance) in resultat:
    print(f"Texte: {texte} (confiance: {confiance:.2f})")