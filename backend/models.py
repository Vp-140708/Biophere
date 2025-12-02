from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    phone = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    
    reviews = relationship('Review', back_populates='user')
    questions = relationship('Question', back_populates='user')

class Review(Base):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    guest_name = Column(String, nullable=True)
    guest_phone = Column(String, nullable=True)
    rating = Column(Integer, nullable=False)
    text = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    admin_reply = Column(Text, nullable=True)

    user = relationship('User', foreign_keys=[user_id], primaryjoin='Review.user_id == User.id', back_populates='reviews')

class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    guest_name = Column(String, nullable=True)
    guest_phone = Column(String, nullable=True)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    admin_reply = Column(Text, nullable=True)
    is_read = Column(Boolean, default=False, nullable=False)

    user = relationship('User', foreign_keys=[user_id], primaryjoin='Question.user_id == User.id', back_populates='questions')

class Specialist(Base):
    __tablename__ = 'specialists'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    position = Column(String, nullable=False)
    specialization = Column(Text, nullable=True)
    workplace = Column(Text, nullable=True)
    education = Column(String, nullable=True)
    extra_qual = Column(Text, nullable=True)
    photo = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False) 