"""Schemas for semantic vector search requests and responses."""

import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class SemanticSearchResultItem(BaseModel):
    """Schema representing a single ranked result in a semantic vector search."""
    meeting_id: uuid.UUID = Field(
        ...,
        description="Unique identifier of the matching meeting"
    )
    meeting_title: str = Field(
        ...,
        description="Title of the matching meeting"
    )
    meeting_date: Optional[datetime] = Field(
        default=None,
        description="The date the meeting took place"
    )
    similarity_score: float = Field(
        ...,
        description="The cosine similarity score calculated as 1 - cosine_distance"
    )
    result_type: str = Field(
        ...,
        description="The type of the matching content: 'summary' or 'transcript'"
    )
    matched_text: str = Field(
        ...,
        description="The actual text content that matched the semantic query"
    )
    summary_preview: Optional[str] = Field(
        default=None,
        description="A preview or portion of the meeting summary"
    )
    speaker: Optional[str] = Field(
        default=None,
        description="Identified speaker for the transcript segment (if result_type is 'transcript')"
    )
    start_time: Optional[float] = Field(
        default=None,
        description="Start time of the segment in seconds (if result_type is 'transcript')"
    )
    end_time: Optional[float] = Field(
        default=None,
        description="End time of the segment in seconds (if result_type is 'transcript')"
    )


class SemanticSearchResponse(BaseModel):
    """Schema representing the list of results returned from a semantic vector search query."""
    results: List[SemanticSearchResultItem] = Field(
        ...,
        description="Ranked semantic search outcomes"
    )
