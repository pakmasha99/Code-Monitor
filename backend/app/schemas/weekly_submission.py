"""
Pydantic schemas for weekly submission API
"""
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class WeeklySubmissionCreate(BaseModel):
    """Schema for creating a weekly submission"""
    week_start_date: date = Field(..., description="Monday of the week (YYYY-MM-DD)")
    code_lines_added: int = Field(default=0, ge=0, description="Lines of code added this week")
    documents_created: int = Field(default=0, ge=0, description="Number of documents created")
    notes: Optional[str] = Field(None, max_length=5000, description="Optional notes about the week")

    class Config:
        json_schema_extra = {
            "example": {
                "week_start_date": "2024-01-15",
                "code_lines_added": 450,
                "documents_created": 3,
                "notes": "Implemented authentication system and wrote API documentation"
            }
        }


class WeeklySubmissionUpdate(BaseModel):
    """Schema for updating a weekly submission"""
    code_lines_added: Optional[int] = Field(None, ge=0)
    documents_created: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = Field(None, max_length=5000)


class WeeklySubmissionResponse(BaseModel):
    """Schema for weekly submission response"""
    id: int
    user_id: int
    week_start_date: date
    code_lines_added: int
    documents_created: int
    notes: Optional[str]

    class Config:
        from_attributes = True


class WeeklySubmissionWithUser(WeeklySubmissionResponse):
    """Schema for weekly submission with user information"""
    user_name: str
    user_email: str
