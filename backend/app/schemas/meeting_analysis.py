"""Pydantic schemas for AI-extracted meeting insights."""

from pydantic import BaseModel, Field
from typing import List, Optional


class Summary(BaseModel):
    """Concise AI-generated summary of the meeting."""
    key_points: List[str] = Field(
        ..., 
        description="Bullet points of the key topics discussed during the meeting"
    )
    high_level_summary: str = Field(
        ..., 
        description="Concise paragraph summarizing the meeting discussions"
    )


class ActionItemResult(BaseModel):
    """Action item extracted from the meeting transcript."""
    description: str = Field(
        ..., 
        description="Description of the action item or task to be completed"
    )
    assignee: Optional[str] = Field(
        None, 
        description="Name or label of the person responsible for this action item"
    )
    due_date: Optional[str] = Field(
        None, 
        description="Deadline or due date if explicitly mentioned (YYYY-MM-DD format if possible), nullable to prevent hallucinations"
    )
    verbatim_quote: Optional[str] = Field(
        None, 
        description="The exact sentence or quote from the transcript supporting this action item"
    )


class DecisionResult(BaseModel):
    """Decision extracted from the meeting transcript."""
    description: str = Field(
        ..., 
        description="Summary of the decision made"
    )
    rationale: Optional[str] = Field(
        None, 
        description="The reasoning or context behind making this decision"
    )
    verbatim_quote: Optional[str] = Field(
        None, 
        description="The exact quote from the transcript supporting this decision"
    )


class RiskResult(BaseModel):
    """Risk identified from the meeting transcript."""
    description: str = Field(
        ..., 
        description="Description of the identified risk, blocker, or concern"
    )
    severity: str = Field(
        ..., 
        description="Risk severity classification: low, medium, high, critical"
    )
    mitigation: Optional[str] = Field(
        None, 
        description="Suggested mitigation strategy or action to manage the risk"
    )
    verbatim_quote: Optional[str] = Field(
        None, 
        description="The exact quote from the transcript supporting this risk"
    )


class ChatSignalResult(BaseModel):
    """Actionable signal from the meeting chat logs/transcript."""
    source: str = Field(
        "meeting_chat", 
        description="Platform origin, e.g., meeting_chat, slack, teams"
    )
    channel_id: str = Field(
        "unknown", 
        description="Channel or conversation identifier"
    )
    message_id: str = Field(
        ..., 
        description="Unique message identifier"
    )
    sender_name: Optional[str] = Field(
        None, 
        description="Display name of the message sender"
    )
    content: str = Field(
        ..., 
        description="Message text content or context from transcript"
    )
    signal_type: str = Field(
        ..., 
        description="Classification category: blocker, decision, risk, general"
    )
    confidence: Optional[float] = Field(
        None, 
        description="Confidence score between 0.0 and 1.0"
    )


class MeetingAnalysis(BaseModel):
    """Unified container for all AI-extracted meeting insights."""
    summary: Summary = Field(
        ..., 
        description="Concise summary details of the meeting"
    )
    action_items: List[ActionItemResult] = Field(
        default_factory=list, 
        description="Extracted action items"
    )
    decisions: List[DecisionResult] = Field(
        default_factory=list, 
        description="Extracted decisions"
    )
    risks: List[RiskResult] = Field(
        default_factory=list, 
        description="Extracted risks"
    )
    chat_signals: List[ChatSignalResult] = Field(
        default_factory=list, 
        description="Extracted chat signals"
    )
