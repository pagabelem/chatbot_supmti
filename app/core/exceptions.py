"""
Gestion centralisée des exceptions pour l'API.
"""
from fastapi import HTTPException, status
from typing import Optional, Any

class NotFoundError(HTTPException):
    """Exception pour ressource non trouvée"""
    def __init__(self, resource: str, resource_id: Optional[str] = None):
        detail = f"{resource} non trouvé"
        if resource_id:
            detail += f" avec ID: {resource_id}"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class ValidationError(HTTPException):
    """Exception pour données invalides"""
    def __init__(self, message: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

class UnauthorizedError(HTTPException):
    """Exception pour non authentifié"""
    def __init__(self, message: str = "Non autorisé"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=message)

class ForbiddenError(HTTPException):
    """Exception pour accès interdit"""
    def __init__(self, message: str = "Accès interdit"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=message)

class ConflictError(HTTPException):
    """Exception pour conflit de données"""
    def __init__(self, message: str):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=message)

class DatabaseError(HTTPException):
    """Exception pour erreurs base de données"""
    def __init__(self, message: str = "Erreur base de données"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)