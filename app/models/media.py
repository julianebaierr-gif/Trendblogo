from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Media(Base):
    __tablename__ = "media"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False)
    url = Column(String(255), nullable=False)
    media_type = Column(String(50), default="image/svg+xml")
    alt_text = Column(String(255), nullable=False)
    caption = Column(String(255), nullable=True)
    prompt = Column(Text, nullable=True)
    provider = Column(String(50), default="procedural_vector")
    width = Column(Integer, default=1200)
    height = Column(Integer, default=630)
    size_bytes = Column(Integer, default=0)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
