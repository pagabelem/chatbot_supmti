from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, Text, DateTime, JSON  # ← JSON ajouté
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from .base import Base


# ======================
# USER
# ======================
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String)
    email = Column(String, unique=True)
    password_hash = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    role = Column(String)
    
    # NOUVEAU: Stocker les préférences utilisateur
    interaction_stats = Column(JSON, default={
        'text_count': 0,
        'voice_count': 0,
        'last_interaction': None,
        'preferred_mode': 'text'
    })

    student = relationship("Student", back_populates="user", uselist=False)


# ======================
# STUDENT
# ======================
class Student(Base):
    __tablename__ = "students"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    average = Column(Float)
    level = Column(String)
    bac_type = Column(String)
    city = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="student")

    conversations = relationship("Conversation", back_populates="student")
    fit_scores = relationship("FitScore", back_populates="student")


# ======================
# INTEREST
# ======================
class Interest(Base):
    __tablename__ = "interests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)


# ======================
# STUDENT INTEREST
# ======================
class StudentInterest(Base):
    __tablename__ = "student_interests"

    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), primary_key=True)
    interest_id = Column(UUID(as_uuid=True), ForeignKey("interests.id"), primary_key=True)


# ======================
# PROGRAM
# ======================
class Program(Base):
    __tablename__ = "programs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    description = Column(Text)
    required_average = Column(Float)
    duration = Column(Integer)
    diploma = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    fit_scores = relationship("FitScore", back_populates="program")


# ======================
# FIT SCORE
# ======================
class FitScore(Base):
    __tablename__ = "fit_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"))
    program_id = Column(UUID(as_uuid=True), ForeignKey("programs.id"))
    score = Column(Float)
    explanation = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="fit_scores")
    program = relationship("Program", back_populates="fit_scores")


# ======================
# CONVERSATION
# ======================
class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"))
    started_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")


# ======================
# MESSAGE
# ======================
class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"))
    content = Column(Text)
    sender = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


# ======================
# DOCUMENT
# ======================
class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String)
    source = Column(String)
    uploaded_at = Column(DateTime, default=datetime.utcnow)


# ======================
# DOCUMENT CHUNK
# ======================
class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    content = Column(Text)
    embedding = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)