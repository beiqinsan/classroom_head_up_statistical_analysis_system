from pydantic import BaseModel

class ChatRequest(BaseModel):
    messages: list
    model: str = "4.0Ultra"
    temperature: float = 0.3
    max_tokens: int = 1024
    stream: bool = False
