# tests/test_tts.py
import openai
from gtts import gTTS
import os

client = openai.OpenAI()

# Option 1: OpenAI TTS
print("🔄 Génération audio avec OpenAI TTS...")
response = client.audio.speech.create(
    model="tts-1",
    voice="alloy",
    input="Bonjour ! Je suis votre conseiller virtuel."
)
response.stream_to_file("openai_test.mp3")
print("✅ Fichier openai_test.mp3 créé")

# Option 2: gTTS
print("\n🔄 Génération audio avec gTTS...")
tts = gTTS(text="Bonjour ! Je suis votre conseiller virtuel.", lang='fr')
tts.save("gtts_test.mp3")
print("✅ Fichier gtts_test.mp3 créé")

print("\n✅ Tests TTS terminés!")
print("📁 Fichiers créés: openai_test.mp3, gtts_test.mp3")