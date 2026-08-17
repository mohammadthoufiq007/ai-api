from enum import Enum
from pydantic import BaseModel, Field

class CategoryEnum(str, Enum):
    work = "work"
    personal = "personal"
    errand = "errand"
    other = "other"

class UrgencyEnum(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"

class TaskEnrichmentRequest(BaseModel):
    description: str = Field(..., min_length=1, max_length=2000, description="Task description to analyze")

class TaskEnrichmentResponse(BaseModel):
    category: CategoryEnum = Field(..., description="The category of the task")
    urgency: UrgencyEnum = Field(..., description="The urgency of the task")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    reason: str = Field(..., description="Short explanation for the categorization")
