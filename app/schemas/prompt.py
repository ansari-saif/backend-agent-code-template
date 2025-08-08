from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class PromptBase(BaseModel):
    user_id: str = Field(..., description="ID of the user making the prompt request")
    prompt_text: str = Field(..., description="The prompt text to send to Gemini API")
    
class PromptCreate(PromptBase):
    pass

class PromptResponse(PromptBase):
    prompt_id: str = Field(..., description="Unique identifier for the prompt")
    response_text: str = Field(..., description="Response from Gemini API")
    created_at: datetime = Field(..., description="When the prompt was created")
    completed_at: Optional[datetime] = Field(None, description="When the response was received")
    
    class Config:
        from_attributes = True

class PromptUpdate(BaseModel):
    response_text: Optional[str] = Field(None, description="Updated response from Gemini API")
    completed_at: Optional[datetime] = Field(None, description="When the response was completed")
