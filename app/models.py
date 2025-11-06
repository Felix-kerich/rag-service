from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class Message(BaseModel):
    """A single message in a conversation"""
    role: str = Field(..., description="Role of the message sender: 'user' or 'assistant'")
    content: str = Field(..., description="Content of the message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    contexts: Optional[List[dict]] = Field(None, description="Retrieved contexts for this message")


class Conversation(BaseModel):
    """A conversation thread"""
    conversation_id: str = Field(..., description="Unique identifier for the conversation")
    user_id: str = Field(..., description="User identifier")
    title: Optional[str] = Field(None, description="Conversation title")
    messages: List[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[dict] = Field(None, description="Additional metadata")


class ConversationSummary(BaseModel):
    """Summary of a conversation for listing"""
    conversation_id: str
    user_id: str
    title: Optional[str]
    message_count: int
    created_at: datetime
    updated_at: datetime
    last_message: Optional[str] = None
