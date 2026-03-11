# tests/test_stt.py
import openai
import os
from gtts import gTTS
from dotenv import load_dotenv

# Charge les variables d'environnement
load_dotenv()

# ✅ CORRECT : on passe le NOM de la variable
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

print("🎤 Création d'un fichier audio de test...")
tts = gTTS(text="Bonjour, je suis intéressé par les programmes d'intelligence artificielle", lang='fr')
tts.save("test_audio_stt.mp3")
print("✅ Fichier test_audio_stt.mp3 créé")

print("\n🔄 Transcription en cours...")
with open("test_audio_stt.mp3", "rb") as f:
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=f
    )
print(f"📝 Texte transcrit: {transcript.text}")