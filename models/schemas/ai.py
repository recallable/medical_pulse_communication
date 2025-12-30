from pydantic import BaseModel, Field


class AiRequest(BaseModel):
    question: str = Field(..., description="问题")
    session_id: str = Field(..., description="会话ID")


class AiResponse(BaseModel):
    answer: str = Field(..., description="答案")
    source: str = Field(..., description="来源")
