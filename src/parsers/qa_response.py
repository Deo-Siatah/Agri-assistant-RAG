from pydantic import BaseModel

class QAResponse(BaseModel):
    answer: str
    source: str
    confidence: str