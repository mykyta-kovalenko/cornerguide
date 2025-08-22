from pydantic import BaseModel
from typing import Optional, Dict, Any
from .enums import Federation, Category, BeltLevel

class RuleChunk(BaseModel):
    content: str
    federation: Federation
    category: Category
    belt_level: Optional[BeltLevel] = None
    technique: Optional[str] = None
    source_page: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    retrieval_score: Optional[float] = None
    rerank_score: Optional[float] = None
    query_used: Optional[str] = None