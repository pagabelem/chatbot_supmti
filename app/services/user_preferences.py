"""
Service de gestion des préférences utilisateur
"""
from sqlalchemy.orm import Session
from app.database.models import User, Student
from app.core.logging import logger
from datetime import datetime, timedelta
from typing import Dict, Optional

class UserPreferenceService:
    """Gère les préférences de l'utilisateur (texte/vocal)"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def update_preference(self, user_id: str, interaction_type: str):
        """
        Met à jour les préférences basées sur le type d'interaction
        interaction_type: 'text' ou 'voice'
        """
        # Récupérer l'utilisateur
        from uuid import UUID
        try:
            user_uuid = UUID(user_id)
            user = self.db.query(User).filter(User.id == user_uuid).first()
            
            if not user:
                return
            
            # Initialiser les stats si nécessaire
            if not hasattr(user, 'interaction_stats'):
                user.interaction_stats = {
                    'text_count': 0,
                    'voice_count': 0,
                    'last_interaction': None,
                    'preferred_mode': 'text'  # Par défaut
                }
            
            # Mettre à jour les compteurs
            if interaction_type == 'text':
                user.interaction_stats['text_count'] += 1
            elif interaction_type == 'voice':
                user.interaction_stats['voice_count'] += 1
            
            user.interaction_stats['last_interaction'] = datetime.now().isoformat()
            
            # Calculer la préférence
            total = user.interaction_stats['text_count'] + user.interaction_stats['voice_count']
            if total > 5:  # Après 5 interactions
                voice_ratio = user.interaction_stats['voice_count'] / total
                
                if voice_ratio > 0.7:  # Plus de 70% de vocaux
                    user.interaction_stats['preferred_mode'] = 'voice'
                elif voice_ratio < 0.3:  # Moins de 30% de vocaux
                    user.interaction_stats['preferred_mode'] = 'text'
                # Sinon, garder l'ancienne préférence
            
            self.db.commit()
            logger.info(f"✅ Préférence mise à jour pour {user_id}: {user.interaction_stats['preferred_mode']}")
            
        except Exception as e:
            logger.error(f"❌ Erreur mise à jour préférence: {e}")
    
    def get_preferred_mode(self, user_id: str) -> str:
        """
        Retourne le mode préféré de l'utilisateur ('text' ou 'voice')
        """
        from uuid import UUID
        try:
            user_uuid = UUID(user_id)
            user = self.db.query(User).filter(User.id == user_uuid).first()
            
            if user and hasattr(user, 'interaction_stats'):
                return user.interaction_stats.get('preferred_mode', 'text')
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération préférence: {e}")
        
        return 'text'  # Mode par défaut
    
    def should_respond_with_voice(self, user_id: str, current_input_type: str) -> bool:
        """
        Détermine si la réponse doit être vocale
        """
        preferred = self.get_preferred_mode(user_id)
        
        # Si l'utilisateur a parlé, on répond en vocal
        if current_input_type == 'voice':
            return True
        
        # Si l'utilisateur préfère le vocal, on répond en vocal
        if preferred == 'voice':
            return True
        
        # Sinon, texte
        return False