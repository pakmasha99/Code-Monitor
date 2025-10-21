"""
Git stats schemas for API request/response
"""
from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, Field, field_validator


class GitStatsResponse(BaseModel):
    """Response schema for git statistics"""
    commits_count: int = Field(..., ge=0, description="Number of commits analyzed")
    files_changed: int = Field(..., ge=0, description="Number of files changed")
    lines_added: int = Field(..., ge=0, description="Total lines added")
    lines_deleted: int = Field(..., ge=0, description="Total lines deleted")
    languages_breakdown: Dict[str, int] = Field(
        default_factory=dict,
        description="Language-wise line count breakdown"
    )
    analyzed_since: datetime = Field(..., description="Start date for analysis")
    repo_url: str = Field(..., description="Repository URL that was analyzed")

    class Config:
        extra = "ignore"
        json_schema_extra = {
            "example": {
                "commits_count": 15,
                "files_changed": 42,
                "lines_added": 850,
                "lines_deleted": 120,
                "languages_breakdown": {
                    "Python": 500,
                    "TypeScript": 350
                },
                "analyzed_since": "2024-01-15T00:00:00",
                "repo_url": "https://github.com/user/repo"
            }
        }
