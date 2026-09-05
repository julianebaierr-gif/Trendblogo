from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from app.database import Base

class GuestPostSubmission(Base):
    __tablename__ = "guest_post_submissions"

    id = Column(Integer, primary_key=True, index=True)
    author_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    website = Column(String(255), nullable=True)
    proposed_title = Column(String(255), nullable=False)
    topic_category = Column(String(100), nullable=False)
    article_outline = Column(Text, nullable=False)
    author_bio = Column(Text, nullable=True)
    message = Column(Text, nullable=True)
    agreed_to_guidelines = Column(Boolean, default=True)
    status = Column(String(30), default="pending")  # pending, approved, rejected, published
    created_at = Column(DateTime, default=datetime.utcnow)

class ContactMessage(Base):
    __tablename__ = "contact_messages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    subject = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    responded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
