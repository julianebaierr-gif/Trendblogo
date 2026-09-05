from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from app.database import get_db
from app.models.article import Article, Category
from app.models.automation import Keyword, GenerationJob
from app.services.keyword_analyzer import KeywordAnalyzer
from app.services.duplicate_checker import DuplicateChecker
from app.services.queue_runner import QueueRunner

router = APIRouter(prefix="/api")

class KeywordAnalyzeRequest(BaseModel):
    keyword: str
    secondary_keywords: Optional[List[str]] = None

class GenerateArticleRequest(BaseModel):
    keyword: str
    secondary_keywords: Optional[str] = ""
    category_id: Optional[int] = None
    tone: Optional[str] = "informative"
    language: Optional[str] = "English"
    target_word_count: Optional[int] = 1500
    template_type: Optional[str] = "ultimate_guide"
    publish_mode: Optional[str] = "published"
    scheduled_delay_hours: Optional[int] = 0

@router.post("/keywords/analyze")
def api_analyze_keyword(req: KeywordAnalyzeRequest):
    if not req.keyword.strip():
        raise HTTPException(status_code=400, detail="Keyword cannot be empty")
    return KeywordAnalyzer.analyze(req.keyword, req.secondary_keywords)

@router.post("/keywords/check-duplicate")
def api_check_duplicate(req: KeywordAnalyzeRequest, db: Session = Depends(get_db)):
    if not req.keyword.strip():
        raise HTTPException(status_code=400, detail="Keyword cannot be empty")
    return DuplicateChecker.check(db, req.keyword)

@router.post("/articles/generate")
def api_generate_article(req: GenerateArticleRequest, db: Session = Depends(get_db)):
    kw_clean = req.keyword.strip()
    if not kw_clean:
        raise HTTPException(status_code=400, detail="Keyword is required")

    # Create GenerationJob
    job = GenerationJob(
        keyword=kw_clean,
        secondary_keywords=req.secondary_keywords,
        category_id=req.category_id,
        tone=req.tone,
        language=req.language,
        target_word_count=req.target_word_count,
        template_type=req.template_type,
        status="processing",
        current_step="Starting automated pipeline"
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Execute synchronous generation pipeline
    result = QueueRunner.execute_job(
        db=db,
        job_id=job.id,
        publish_mode=req.publish_mode or "published",
        scheduled_delay_hours=req.scheduled_delay_hours or 0
    )

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Generation failed"))

    article = db.query(Article).filter(Article.id == result["article_id"]).first()
    return {
        "success": True,
        "article_id": article.id,
        "title": article.title,
        "slug": article.slug,
        "url": f"/blog/{article.slug}",
        "quality_score": article.quality_score,
        "word_count": article.word_count,
        "featured_image": article.featured_image
    }

@router.post("/queue/run-all")
def api_run_queue(db: Session = Depends(get_db)):
    pending_jobs = db.query(GenerationJob).filter(GenerationJob.status.in_(["pending", "failed"])).all()
    processed = []
    for job in pending_jobs:
        res = QueueRunner.execute_job(db, job.id)
        processed.append({"job_id": job.id, "keyword": job.keyword, "result": res})
    return {"processed_count": len(processed), "details": processed}

@router.get("/search/suggest")
def api_search_suggest(q: str = Query("", min_length=2), db: Session = Depends(get_db)):
    pattern = f"%{q.strip()}%"
    results = db.query(Article.id, Article.title, Article.slug, Article.featured_image).filter(
        Article.status == "published",
        or_(Article.title.ilike(pattern), Article.primary_keyword.ilike(pattern))
    ).limit(5).all()
    
    return [{"id": r.id, "title": r.title, "slug": r.slug, "image": r.featured_image} for r in results]
