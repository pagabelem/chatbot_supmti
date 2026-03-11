# tests/test_tts_simple.py
from gtts import gTTS
import os

print("🔄 Génération audio avec gTTS...")

# Version multilingue
texts = [
    ("Bonjour, je suis votre conseiller virtuel.", "fr"),
    ("Hello, I am your virtual advisor.", "en"),
    ("Salam, ana mostacharek dialkom.", "ar"),
]

for i, (text, lang) in enumerate(texts):
    print(f"\n📝 Texte {i+1}: {text}")
    tts = gTTS(text=text, lang=lang, slow=False)
    filename = f"test_audio_{lang}.mp3"
    tts.save(filename)
    print(f"✅ Fichier créé: {filename}")

print("\n🎉 3 fichiers audio créés !")
print("📁 Fichiers: test_audio_fr.mp3, test_audio_en.mp3, test_audio_ar.mp3")