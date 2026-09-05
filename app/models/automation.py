from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from app.database import Base

class Keyword(Base):
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(200), unique=True, index=True, nullable=False)
    search_intent = Column(String(50), default="informational")
    target_audience = Column(String(100), default="General Professional")
    priority = Column(Integer, default=1)
    status = Column(String(30), default="queued", index=True)  # queued, processing, completed, failed
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(200), nullable=False)
    secondary_keywords = Column(Text, nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    tone = Column(String(50), default="informative")
    language = Column(String(50), default="English")
    target_word_count = Column(Integer, default=1500)
    template_type = Column(String(50), default="ultimate_guide")
    
    # Execution Tracking
    status = Column(String(30), default="pending", index=True) # pending, processing, completed, failed
    current_step = Column(String(80), default="Initialized")
    progress = Column(Integer, default=0) # 0 to 100
    
    result_article_id = Column(Integer, ForeignKey("articles.id", ondelete="SET NULL"), nullable=True)
    error_message = Column(Text, nullable=True)
    logs = Column(Text, default="Job created.")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AIUsage(Base):
    __tablename__ = "ai_usage"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(50), default="openai")
    model = Column(String(80), default="gpt-4o-mini")
    operation = Column(String(80), nullable=False)  # article_text, outline, images, qc, seo
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    estimated_cost = Column(Float, default=0.0)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
