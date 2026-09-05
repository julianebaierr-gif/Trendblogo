from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class InternalLink(Base):
    __tablename__ = "internal_links"

    id = Column(Integer, primary_key=True, index=True)
    source_article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    target_article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    anchor_text = Column(String(255), nullable=False)
    target_url = Column(String(255), nullable=False)
    context_sentence = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    source_article = relationship("Article", foreign_keys=[source_article_id], back_populates="internal_links_out")
    target_article = relationship("Article", foreign_keys=[target_article_id])

class ExternalLink(Base):
    __tablename__ = "external_links"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    anchor_text = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)
    domain = Column(String(150), nullable=False)
    source_type = Column(String(50), default="authoritative")  # official_docs, wikipedia, research, gov, edu
    is_nofollow = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    article = relationship("Article", back_populates="external_links")

class RelatedPost(Base):
    __tablename__ = "related_posts"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    related_article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    relevance_score = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    article = relationship("Article", foreign_keys=[article_id])
    related_article = relationship("Article", foreign_keys=[related_article_id])
