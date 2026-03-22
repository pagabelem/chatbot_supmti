from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Remplacez l'URL par celle-ci en vérifiant bien le mot de passe
# On ajoute ?client_encoding=utf8 à la fin
DATABASE_URL = "postgresql://postgres:BASILO.pag@localhost:5432/chatbot_db"

engine = create_engine(
    DATABASE_URL,
    # Cette option force psycopg2 à utiliser l'encodage correct
    connect_args={"options": "-c client_encoding=utf8"}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()