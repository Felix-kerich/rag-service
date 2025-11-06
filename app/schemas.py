from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class Document(BaseModel):
    """Document for ingestion"""
    id: Optional[str] = None
    text: str
    metadata: Optional[Dict[str, Any]] = None


class IngestRequest(BaseModel):
    """Request to ingest documents"""
    documents: List[Document]


class QueryRequest(BaseModel):
    """Request to query the RAG system"""
    question: str = Field(..., description="The question to ask")
    k: int = Field(4, description="Number of context documents to retrieve", ge=1, le=10)
    conversation_id: Optional[str] = Field(None, description="Conversation ID for history tracking")
    user_id: str = Field(..., description="User identifier")


class QueryResponse(BaseModel):
    """Response from a query"""
    answer: str
    contexts: List[Dict[str, Any]]
    conversation_id: str
    message_id: Optional[str] = None


class CreateConversationRequest(BaseModel):
    """Request to create a new conversation"""
    user_id: str = Field(..., description="User identifier")
    title: Optional[str] = Field(None, description="Optional conversation title")
    metadata: Optional[Dict[str, Any]] = None


class UpdateConversationRequest(BaseModel):
    """Request to update a conversation"""
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: str
    services: Dict[str, str]
