from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class UserRole(str, enum.Enum):
    student = "student"
    teacher = "teacher"

class DocStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class EventStatus(str, enum.Enum):
    active = "active"
    upcoming = "upcoming"
    closed = "closed"

class EventCategory(str, enum.Enum):
    sport = "sport"
    cultural = "cultural"
    science = "science"
    volunteer = "volunteer"
    personal = "personal"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    full_name = Column(String(200), nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    hashed_password = Column(String(300), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.student)
    group = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    participations = relationship("Participation", back_populates="student", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="teacher")

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True)
    title = Column(String(300), nullable=False)
    description = Column(Text)
    department = Column(String(200))
    deadline = Column(String(50))
    doc_requirements = Column(Text)
    status = Column(Enum(EventStatus), default=EventStatus.active)
    category = Column(Enum(EventCategory), default=EventCategory.science)
    teacher_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    teacher = relationship("User", back_populates="events")
    participations = relationship("Participation", back_populates="event", cascade="all, delete-orphan")

class Participation(Base):
    __tablename__ = "participations"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    event_id = Column(Integer, ForeignKey("events.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    student = relationship("User", back_populates="participations")
    event = relationship("Event", back_populates="participations")
    documents = relationship("Document", back_populates="participation", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    participation_id = Column(Integer, ForeignKey("participations.id"))
    filename = Column(String(300), nullable=True)
    original_name = Column(String(300))
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    doc_type = Column(String(20), default="file")  # "file" or "link"
    link_url = Column(String(500), nullable=True)
    status = Column(Enum(DocStatus), default=DocStatus.pending)
    teacher_comment = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    participation = relationship("Participation", back_populates="documents")
