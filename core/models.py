import uuid
from typing import List, Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB

class User(SQLModel, table=True):
    """The secure identity and credential vault for a user."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    
    # never accidentally use them without passing them through the decryptor first.
    encrypted_llm_api_key: Optional[str] = None
    encrypted_tavily_api_key: Optional[str] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserProfile(SQLModel, table=True):
    """The dynamic 'Brain' for a user."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # Foreign Key linking this brain to a specific user
    user_id: uuid.UUID = Field(foreign_key="user.id", unique=True, index=True)
    
    # We use Postgres JSONB so you can easily append new strings to these arrays
    core_interests: list = Field(default=[], sa_column=Column(JSONB))
    focus_areas: list = Field(default=[], sa_column=Column(JSONB))
    avoid_topics: list = Field(default=[], sa_column=Column(JSONB))
    rss_feeds: list = Field(default=[], sa_column=Column(JSONB))

class ArticleState(SQLModel, table=True):
    """Tracks which user has received which article (Replaces Qdrant 'emailed' tag)"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    
    # The Vector ID from Qdrant
    qdrant_doc_id: str = Field(index=True) 
    
    emailed: bool = Field(default=False)
    feedback_given: Optional[str] = Field(default=None) # e.g., 'explore', 'prune'