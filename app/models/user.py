import hashlib
import os
import secrets
from datetime import datetime
from typing import Tuple, Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False, default="Administrator")
    password_hash = Column(String(255), nullable=False)
    salt = Column(String(64), nullable=False)
    role = Column(String(20), default="admin", nullable=False)
    is_active = Column(Boolean, default=True)
    session_token = Column(String(128), unique=True, nullable=True)
    
    # Author Profile Attributes
    slug = Column(String(100), unique=True, index=True, nullable=True)
    bio = Column(Text, nullable=True)
    avatar = Column(String(255), nullable=True)
    title_designation = Column(String(100), nullable=True, default="Principal Technology Editor")
    twitter = Column(String(100), nullable=True)
    github = Column(String(100), nullable=True)
    linkedin = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        if not salt:
            salt = secrets.token_hex(16)
        hashed = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100000
        ).hex()
        return hashed, salt

    def verify_password(self, password: str) -> bool:
        test_hash, _ = self.hash_password(password, self.salt)
        return secrets.compare_digest(test_hash, self.password_hash)

    def generate_session(self) -> str:
        self.session_token = secrets.token_urlsafe(48)
        return self.session_token
