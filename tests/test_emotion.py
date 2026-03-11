# tests/test_emotion.py
from transformers import pipeline
import json

print("🔄 Chargement du modèle d'émotions...")
classifier = pipeline(
    "text-classification", 
    model="j-hartmann/emotion-english-distilroberta-base",
    top_k=None,
    device="cpu"
)
print("✅ Modèle chargé !\n")

test_messages = [
    "I am so happy with this school!",
    "I'm really frustrated, I don't understand anything",
    "Wow, that's amazing news!",
    "Je suis très content de cette école",
    "Salam, kifash n9der n3awnkom?"
]

for msg in test_messages:
    print(f"📝 Message: {msg}")
    results = classifier(msg)[0]
    sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)
    print("🎭 Émotions détectées:")
    for r in sorted_results[:3]:
        print(f"   {r['label']}: {r['score']:.3f}")
    print("-" * 50)