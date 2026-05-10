# """
# Route pour tester le service STT
# """
# from fastapi import APIRouter, UploadFile, File, HTTPException
# from app.services.stt_service import STTService
# from app.core.logging import logger

# router = APIRouter(prefix="/test-stt", tags=["test"])

# @router.post("/transcribe")
# async def test_transcription(
#     file: UploadFile = File(..., description="Fichier audio à tester")
# ):
#     """
#     Teste la transcription vocale
#     """
#     logger.info(f"🧪 Test STT - Fichier: {file.filename}")
    
#     if not file.content_type.startswith('audio/'):
#         raise HTTPException(400, "Le fichier doit être un fichier audio")
    
#     stt = STTService()
#     audio_bytes = await file.read()
    
#     result = await stt.transcribe_with_detection(audio_bytes)
#     return result

# @router.get("/status")
# async def test_status():
#     """
#     Vérifie le statut du service STT
#     """
#     stt = STTService()
#     return await stt.test_connection()



# ============================================================
# app/api/routes/voice.py
# Routes Voice : /api/voice/transcribe + /api/voice/chat + /api/voice/tts
# À ajouter dans main.py :
#   from app.api.routes.voice import router as voice_router
#   app.include_router(voice_router, prefix="/api")
# ============================================================

# import os
# import re
# import base64
# import tempfile
# import unicodedata
# from fastapi import APIRouter, HTTPException, UploadFile, File, Form
# from fastapi.responses import JSONResponse
# from pydantic import BaseModel
# from typing import Optional
# from openai import OpenAI
# from dotenv import load_dotenv

# load_dotenv()
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# router = APIRouter(prefix="/voice", tags=["voice"])

# # ── Voix disponibles par langue ──────────────────────────────
# VOICES_BY_LANG = {
#     "fr": [
#         {"id": "nova",    "label": "Nova",    "desc": "Naturelle, chaleureuse"},
#         {"id": "shimmer", "label": "Shimmer", "desc": "Douce, posée"},
#         {"id": "echo",    "label": "Echo",    "desc": "Claire, professionnelle"},
#     ],
#     "ar": [
#         {"id": "onyx",  "label": "Onyx",  "desc": "Grave, expressive (darija)"},
#         {"id": "alloy", "label": "Alloy", "desc": "Posée, fluide"},
#     ],
#     "en": [
#         {"id": "fable", "label": "Fable", "desc": "Storytelling, engaging"},
#         {"id": "echo",  "label": "Echo",  "desc": "Clear, professional"},
#         {"id": "nova",  "label": "Nova",  "desc": "Warm, friendly"},
#     ],
# }

# # ── Prompts Whisper par langue ────────────────────────────────
# WHISPER_PROMPTS = {
#     "fr": (
#         "Conversation d'orientation académique à SUPMTI Meknès. "
#         "Filières : MGE, MDI, FACG, MRI, IISI, IISIC, IISRT. "
#         "Mots clés : filière, admission, bourse, FitScore, BAC, licence."
#     ),
#     "ar": (
#         "محادثة توجيه أكاديمي بالدارجة المغربية. "
#         "wach, kayn, bghit, chno, 3ndek, mzyan, safi, labas, zwina, dyali, filiere, supmti, bac."
#     ),
#     "en": (
#         "Academic orientation conversation at SUPMTI Meknes. "
#         "Programs: MGE, MDI, FACG, MRI, IISI, IISIC, IISRT. "
#         "Keywords: program, admission, scholarship, FitScore, degree."
#     ),
# }

# # ── Patterns d'hallucination Whisper ─────────────────────────
# HALLUCINATION_PATTERNS = [
#     "sous-titres", "sous titres", "abonnez", "merci d'avoir",
#     "thanks for watching", "transcription by", "www.", "http",
#     "mots courants", "wach, kayn", "kayn, bghit", "bghit, chno",
#     "labas, zwina", "conversation sur l'orientation",
#     "academic orientation conversation",
# ]

# def _clean_for_tts(text: str) -> str:
#     """Supprime markdown et emojis pour TTS propre."""
#     text = re.sub(r'#{1,6}\s*', '', text)
#     text = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)
#     text = re.sub(r'^\s*[-•►]\s*', '', text, flags=re.MULTILINE)
#     text = re.sub(r'`{1,3}.*?`{1,3}', '', text, flags=re.DOTALL)
#     text = re.sub(r'[─═━┄]+', '', text)
#     # Emojis
#     text = re.sub(r'[\U0001F000-\U0001FFFF]', '', text)
#     text = re.sub(r'[\U00002600-\U000027BF]', '', text)
#     text = re.sub(r'\n{2,}', '. ', text)
#     text = re.sub(r'\s+', ' ', text).strip()
#     return text[:4000]

# def _is_hallucination(text: str) -> bool:
#     if not text or len(text.strip()) < 2:
#         return True
#     low = text.lower()
#     for pat in HALLUCINATION_PATTERNS:
#         if pat in low:
#             return True
#     # Répétition : si la 2ème moitié commence comme la 1ère
#     mid = len(text) // 2
#     if mid > 20 and text[mid:mid+20] in text[:mid]:
#         return True
#     return False


# # ============================================================
# # GET /api/voice/voices — liste des voix disponibles
# # ============================================================
# @router.get("/voices")
# async def get_voices():
#     """Retourne les voix disponibles par langue."""
#     return {"voices": VOICES_BY_LANG}


# # ============================================================
# # POST /api/voice/transcribe — Whisper STT
# # ============================================================
# @router.post("/transcribe")
# async def transcribe_audio(
#     audio: UploadFile = File(...),
#     lang: str = Form(default="fr"),
# ):
#     """
#     Transcrit un fichier audio via Whisper.
#     lang : fr | ar | en
#     """
#     audio_bytes = await audio.read()

#     if len(audio_bytes) < 600:
#         return {"text": "", "no_speech": True}

#     # Langue Whisper
#     whisper_lang_map = {"fr": "fr", "ar": "ar", "en": "en"}
#     whisper_lang     = whisper_lang_map.get(lang, "fr")
#     prompt           = WHISPER_PROMPTS.get(lang, WHISPER_PROMPTS["fr"])

#     # Écrire dans un fichier temporaire
#     suffix = ".webm"
#     if audio.filename:
#         ext = os.path.splitext(audio.filename)[-1]
#         if ext in (".m4a", ".mp3", ".wav", ".ogg", ".webm"):
#             suffix = ext

#     with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
#         tmp.write(audio_bytes)
#         tmp_path = tmp.name

#     try:
#         with open(tmp_path, "rb") as f:
#             result = client.audio.transcriptions.create(
#                 model="whisper-1",
#                 file=f,
#                 language=whisper_lang,
#                 prompt=prompt,
#                 response_format="verbose_json",
#                 temperature=0.0,
#             )

#         text      = result.text.strip()
#         no_speech = getattr(result, "no_speech_prob", 0) > 0.7

#         if no_speech or _is_hallucination(text):
#             return {"text": "", "no_speech": True}

#         return {"text": text, "no_speech": False}

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Erreur Whisper : {str(e)}")
#     finally:
#         os.unlink(tmp_path)


# # ============================================================
# # POST /api/voice/chat — GPT + TTS pour le Live
# # ============================================================
# class VoiceChatRequest(BaseModel):
#     message:   str
#     lang:      str = "fr"
#     voice:     str = "nova"
#     student_id: Optional[str] = None

# @router.post("/chat")
# async def voice_chat(req: VoiceChatRequest):
#     """
#     Reçoit un message texte (issu de Whisper),
#     génère une réponse GPT et retourne l'audio TTS en base64.
#     """
#     if not req.message.strip():
#         raise HTTPException(status_code=400, detail="Message vide.")

#     # ── Prompt système selon la langue ───────────────────────
#     system_prompts = {
#         "fr": (
#             "Tu es SAMI, conseiller académique de SUPMTI Meknès. "
#             "Réponds en français de façon concise (2-3 phrases max). "
#             "Filières : IISI (BAC+3 info), MGE/MDI (BAC+3 management), "
#             "IISIC/IISRT (BAC+5 info), FACG/MRI (BAC+5 management). "
#             "Pas de markdown, pas d'emojis. Parle naturellement."
#         ),
#         "ar": (
#             "نتا SAMI، مستشار أكاديمي د SUPMTI Meknès. "
#             "جاوب بالدارجة المغربية بشكل مختصر (2-3 جمل). "
#             "الفيليار : IISI, MGE, MDI, IISIC, IISRT, FACG, MRI. "
#             "ما تكتبش markdown ولا emojis."
#         ),
#         "en": (
#             "You are SAMI, academic advisor at SUPMTI Meknes. "
#             "Answer in English concisely (2-3 sentences max). "
#             "Programs: IISI (BAC+3 CS), MGE/MDI (BAC+3 management), "
#             "IISIC/IISRT (BAC+5 CS), FACG/MRI (BAC+5 management). "
#             "No markdown, no emojis. Speak naturally."
#         ),
#     }
#     system = system_prompts.get(req.lang, system_prompts["fr"])

#     # ── Appel GPT ─────────────────────────────────────────────
#     try:
#         gpt_resp = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {"role": "system", "content": system},
#                 {"role": "user",   "content": req.message},
#             ],
#             temperature=0.6,
#             max_tokens=300,
#         )
#         text_response = gpt_resp.choices[0].message.content.strip()
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Erreur GPT : {str(e)}")

#     # ── Nettoyage pour TTS ────────────────────────────────────
#     clean_text = _clean_for_tts(text_response)

#     # ── Validation voix ───────────────────────────────────────
#     all_voices = [v["id"] for vlist in VOICES_BY_LANG.values() for v in vlist]
#     voice = req.voice if req.voice in all_voices else "nova"

#     # ── TTS ───────────────────────────────────────────────────
#     try:
#         tts_resp = client.audio.speech.create(
#             model="tts-1",
#             voice=voice,
#             input=clean_text,
#             response_format="mp3",
#             speed=1.05,
#         )
#         audio_b64 = base64.b64encode(tts_resp.content).decode("utf-8")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Erreur TTS : {str(e)}")

#     return {
#         "text":  text_response,   # texte brut pour affichage dans le chat
#         "audio": audio_b64,       # audio base64 pour lecture immédiate
#     }


# # ============================================================
# # POST /api/voice/tts — TTS simple (preview voix)
# # ============================================================
# class TTSRequest(BaseModel):
#     text:  str
#     voice: str = "nova"

# @router.post("/tts")
# async def text_to_speech(req: TTSRequest):
#     """TTS simple — utilisé pour la preview des voix dans le modal."""
#     clean = _clean_for_tts(req.text)
#     if not clean:
#         raise HTTPException(status_code=400, detail="Texte vide.")

#     all_voices = [v["id"] for vlist in VOICES_BY_LANG.values() for v in vlist]
#     voice = req.voice if req.voice in all_voices else "nova"

#     try:
#         tts_resp = client.audio.speech.create(
#             model="tts-1",
#             voice=voice,
#             input=clean,
#             response_format="mp3",
#             speed=1.0,
#         )
#         audio_b64 = base64.b64encode(tts_resp.content).decode("utf-8")
#         return {"audio": audio_b64}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Erreur TTS : {str(e)}")



import os
import re
import base64
import tempfile
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
router = APIRouter(prefix="/api/voice", tags=["voice"])

# ── Voix disponibles ──────────────────────────────────────────
VOICES_BY_LANG = {
    "fr":     [{"id": "nova",    "label": "Nova",    "desc": "Naturelle, chaleureuse"},
               {"id": "shimmer", "label": "Shimmer", "desc": "Douce, posée"},
               {"id": "echo",    "label": "Echo",    "desc": "Claire, professionnelle"}],
    "darija": [{"id": "nova",    "label": "Nova",    "desc": "Darija - naturelle"},
               {"id": "onyx",    "label": "Onyx",    "desc": "Darija - profonde"},
               {"id": "alloy",   "label": "Alloy",   "desc": "Darija - fluide"}],
    "en":     [{"id": "alloy",   "label": "Alloy",   "desc": "Balanced"},
               {"id": "fable",   "label": "Fable",   "desc": "Warm & engaging"},
               {"id": "nova",    "label": "Nova",    "desc": "Warm, friendly"}],
}

# ── Prompts Whisper ───────────────────────────────────────────
# CLEF : pour la darija, on force Whisper à transcrire en alphabet latin
# en lui donnant des exemples de darija latine dans le prompt
WHISPER_PROMPTS = {
    "fr": (
        "Conversation d'orientation académique à SUPMTI Meknès. "
        "Filières : MGE, MDI, FACG, MRI, IISI, IISIC, IISRT. "
        "Mots clés : filière, admission, bourse, FitScore, BAC, licence, moyenne."
    ),
    "darija": (
        # On donne des exemples de mots darija EN ALPHABET LATIN
        # Cela force Whisper à transcrire en latin au lieu de l'arabe
        "Transcris en alphabet latin. "
        "wach kayn bghit chno 3ndek mzyan safi labas zwina dyali ndkhol "
        "filiere supmti bac scolarite bourse mdrassa moyenne licence "
        "wakha iyeh khoya khti dyal bzzaf daba dial hnouma "
        "IISI MGE MDI IISIC IISRT FACG MRI "
        "Utilise les chiffres 3 7 9 pour les sons arabes en darija latine."
    ),
    "en": (
        "Academic orientation conversation at SUPMTI Meknes. "
        "Programs: MGE, MDI, FACG, MRI, IISI, IISIC, IISRT. "
        "Keywords: program, admission, scholarship, FitScore, degree, average."
    ),
}

# Mapping langue frontend → code langue Whisper
WHISPER_LANG_MAP = {
    "fr":           "fr",
    "darija":       "ar",   # Whisper détecte l'arabe marocain, mais notre prompt le force au latin
    "darija_latin": "ar",   # idem
    "darija_arabe": "ar",
    "en":           "en",
    "ar":           "ar",
}

# Mapping langue → prompt
PROMPT_MAP = {
    "fr":           "fr",
    "darija":       "darija",
    "darija_latin": "darija",
    "darija_arabe": "darija",
    "en":           "en",
    "ar":           "darija",
}

# ── Patterns d'hallucination ──────────────────────────────────
HALLUCINATION_PATTERNS = [
    "sous-titres", "amara.org", "abonnez", "merci d'avoir regardé",
    "thanks for watching", "transcription by", "mots courants",
    "wach, kayn", "kayn, bghit", "filières: mge",
    "conversation sur l'orientation", "academic orientation conversation",
    "droits réservés",
]

def _is_hallucination(text: str) -> bool:
    if not text or len(text.strip()) < 2:
        return True
    low = text.lower()
    for pat in HALLUCINATION_PATTERNS:
        if pat in low:
            return True
    # Répétition
    mid = len(text) // 2
    if mid > 20 and text[mid:mid + 20] in text[:mid]:
        return True
    return False


def _clean_for_tts(text: str) -> str:
    """Supprime markdown et emojis pour un TTS propre."""
    text = re.sub(r'#{1,6}\s*', '', text)
    text = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)
    text = re.sub(r'^\s*[-•►]\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'`{1,3}.*?`{1,3}', '', text, flags=re.DOTALL)
    text = re.sub(r'[─═━┄]+', '', text)
    text = re.sub(r'[\U0001F000-\U0001FFFF]', '', text)
    text = re.sub(r'[\U00002600-\U000027BF]', '', text)
    text = re.sub(r'\n{2,}', '. ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:4000]


# ============================================================
# GET /api/voice/voices
# ============================================================
@router.get("/voices")
async def get_voices():
    return {"voices": VOICES_BY_LANG}


# ============================================================
# POST /api/voice/transcribe — Whisper STT
# ============================================================
@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    lang:  str        = Form(default="fr"),
):
    """
    Transcrit un fichier audio.
    lang : fr | darija | darija_latin | en | ar
    
    Pour la darija : utilise un prompt spécial qui force
    Whisper à transcrire en alphabet latin (pas arabe).
    """
    audio_bytes = await audio.read()
    if len(audio_bytes) < 600:
        return {"text": "", "no_speech": True}

    # Déterminer la langue Whisper et le prompt
    whisper_lang = WHISPER_LANG_MAP.get(lang, "fr")
    prompt_key   = PROMPT_MAP.get(lang, "fr")
    prompt       = WHISPER_PROMPTS.get(prompt_key, WHISPER_PROMPTS["fr"])

    # Extension du fichier
    suffix = ".webm"
    if audio.filename:
        ext = os.path.splitext(audio.filename)[-1].lower()
        if ext in (".m4a", ".mp3", ".wav", ".ogg", ".webm", ".mp4"):
            suffix = ext

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            result = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language=whisper_lang,
                prompt=prompt,
                response_format="verbose_json",
                temperature=0.0,
            )

        text      = result.text.strip() if result.text else ""
        no_speech = getattr(result, "no_speech_prob", 0.0) > 0.7

        if no_speech or _is_hallucination(text):
            return {"text": "", "no_speech": True}

        # Pour la darija : vérifier que le résultat est bien en latin
        # Si Whisper a quand même renvoyé de l'arabe malgré le prompt,
        # on convertit les chiffres-lettres arabes mais on garde le latin
        if lang in ("darija", "darija_latin") and text:
            arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
            total_chars  = len([c for c in text if c.isalpha()])
            if total_chars > 0 and (arabic_chars / total_chars) > 0.5:
                # Trop d'arabe → le résultat n'est pas en latin
                # On retourne quand même mais on le signale
                return {
                    "text": text,
                    "no_speech": False,
                    "warning": "arabic_detected",
                }

        return {"text": text, "no_speech": False}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur Whisper: {str(e)}")
    finally:
        try: os.unlink(tmp_path)
        except: pass


# ============================================================
# POST /api/voice/chat — GPT + TTS
# ============================================================
class VoiceChatRequest(BaseModel):
    message:    str
    lang:       str = "fr"
    voice:      str = "nova"
    student_id: Optional[str] = None

@router.post("/chat")
async def voice_chat(req: VoiceChatRequest):
    """
    Reçoit un message texte, génère une réponse GPT + TTS.
    Supporte : fr | darija | darija_latin | en | ar
    """
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message vide.")

    # ── Prompt système selon la langue ───────────────────────
    system_prompts = {
        "fr": (
            "Tu es SAMI, conseiller académique de SUPMTI Meknès. "
            "Réponds en français de façon concise (2-3 phrases max). "
            "Filières : IISI (BAC+3 info), MGE/MDI (BAC+3 management), "
            "IISIC/IISRT (BAC+5 info), FACG/MRI (BAC+5 management). "
            "Pas de markdown. Parle naturellement."
        ),
        "darija": (
            # CORRECTION : prompt darija LATINE — pas d'arabe
            "Nta SAMI, l-mstchar d-l-qra f SUPMTI Meknes. "
            "REGLE ABSOLUE : Kteb GHER b-l-alfaba latin (A-Z + chiffres 3/7/9). "
            "ZÉRO lettre arabe. Darija marocaine réelle mélangée avec mots français. "
            "Jaweb b-2-3 joumla maximum. "
            "Filieres : IISI (BAC+3 info), MGE/MDI (BAC+3 management), "
            "IISIC/IISRT (BAC+5 info), FACG/MRI (BAC+5 management). "
            "Machi markdown. Machi emoji bzzaf. "
            "Exemples : 'Labas, kifach nqderha n3awnek?' / 'Wach 3ndek le BAC ?' / "
            "'MGE zwina bzzaf ila bghiti l-management w l-gestion.'"
        ),
        "darija_latin": (  # alias
            "Nta SAMI, l-mstchar d-l-qra f SUPMTI Meknes. "
            "REGLE ABSOLUE : Kteb GHER b-l-alfaba latin. ZÉRO lettre arabe. "
            "Darija marocaine + mots français. 2-3 joumla. Machi markdown."
        ),
        "en": (
            "You are SAMI, academic advisor at SUPMTI Meknes. "
            "Answer in English concisely (2-3 sentences max). "
            "Programs: IISI (BAC+3 CS), MGE/MDI (BAC+3 management), "
            "IISIC/IISRT (BAC+5 CS), FACG/MRI (BAC+5 management). "
            "No markdown. Speak naturally."
        ),
    }
    # Fallback
    system = system_prompts.get(req.lang, system_prompts["fr"])

    # ── Appel GPT ─────────────────────────────────────────────
    try:
        gpt_resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": req.message},
            ],
            temperature=0.65,
            max_tokens=300,
        )
        text_response = gpt_resp.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur GPT: {str(e)}")

    clean_text = _clean_for_tts(text_response)

    # ── Validation voix ───────────────────────────────────────
    all_voices = {v["id"] for vlist in VOICES_BY_LANG.values() for v in vlist}
    voice = req.voice if req.voice in all_voices else "nova"

    # ── TTS ───────────────────────────────────────────────────
    try:
        tts_resp = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=clean_text,
            response_format="mp3",
            speed=1.05,
        )
        audio_b64 = base64.b64encode(tts_resp.content).decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur TTS: {str(e)}")

    return {
        "text":  text_response,
        "audio": audio_b64,
    }


# ============================================================
# POST /api/voice/tts — TTS simple
# ============================================================
class TTSRequest(BaseModel):
    text:  str
    voice: str = "nova"

@router.post("/tts")
async def text_to_speech(req: TTSRequest):
    """TTS simple — preview voix + lecture messages chat."""
    clean = _clean_for_tts(req.text)
    if not clean:
        raise HTTPException(status_code=400, detail="Texte vide.")

    all_voices = {v["id"] for vlist in VOICES_BY_LANG.values() for v in vlist}
    voice = req.voice if req.voice in all_voices else "nova"

    try:
        tts_resp = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=clean,
            response_format="mp3",
            speed=1.0,
        )
        return {"audio": base64.b64encode(tts_resp.content).decode("utf-8")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur TTS: {str(e)}")