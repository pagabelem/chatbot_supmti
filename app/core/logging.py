"""
Configuration du logging pour l'application.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime

# Créer le dossier logs s'il n'existe pas
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Nom du fichier de log avec date
log_filename = log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"

def setup_logging():
    """
    Configure le logging pour l'application.
    - Logs dans fichier (niveau DEBUG)
    - Logs dans console (niveau INFO)
    """
    # Format des logs
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler pour fichier
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setFormatter(log_format)
    file_handler.setLevel(logging.DEBUG)
    
    # Handler pour console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    console_handler.setLevel(logging.INFO)
    
    # Configuration du root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Logger pour l'application
    logger = logging.getLogger("chatbot")
    logger.info("✅ Logging configuré avec succès")
    
    return logger

# Initialiser le logging
logger = setup_logging()