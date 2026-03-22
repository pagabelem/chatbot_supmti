from pydantic import BaseModel
from typing import List, Optional

class PsychoAnswerRequest(BaseModel):
    """
    Schéma de validation pour les réponses au test psychotechnique.
    """
    user_id: str
    current_step: int
    answers: List[str]
    last_answer: Optional[str] = None

class UserProfileSchema(BaseModel):
    """
    Schéma pour le profil utilisateur (optionnel, pour ton service profile).
    """
    full_name: str
    email: str
    role: Optional[str] = "student"