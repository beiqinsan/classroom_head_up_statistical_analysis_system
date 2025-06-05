from pydantic import BaseModel
from datetime import datetime

class DetectionCountResponse(BaseModel):
    id: int
    timestamp: datetime
    lookup_count: int
    other_count: int

    class Config:
        from_attributes =True