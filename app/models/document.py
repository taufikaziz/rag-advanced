# Document models

from __future__ import annotations
from datetime import datetime
from typing import Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str
    metadata: dict = Field(default_factory=dict)
    source: Optional[str] = None
    embedding: Optional[list[float]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentChunk(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    document_id: str
    content: str
    chunk_index: int = 0
    metadata: dict = Field(default_factory=dict)
    embedding: Optional[list[float]] = None
