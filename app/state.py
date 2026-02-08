from pydantic import BaseModel
from typing import List, Dict, Optional

class ResearchState(BaseModel):
    topic: str
    plan: List[str] = []
    current_step: int = 0
    sources: List[Dict] = []
    report: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[float] = 0.0
