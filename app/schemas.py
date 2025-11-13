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


class AdviceContext(BaseModel):
    """Structured analytics context from ShambaBora"""
    crop_type: str
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    total_expenses: Optional[float] = None
    total_revenue: Optional[float] = None
    net_profit: Optional[float] = None
    profit_margin: Optional[float] = None
    total_yield: Optional[float] = None
    average_yield_per_unit: Optional[float] = None
    best_yield: Optional[float] = None
    worst_yield: Optional[float] = None
    expenses_by_category: Optional[Dict[str, float]] = None
    expenses_by_growth_stage: Optional[Dict[str, float]] = None
    prior_recommendations: Optional[List[str]] = None
    soil_type: Optional[str] = None
    soil_ph: Optional[float] = None
    rainfall_mm: Optional[float] = None
    location: Optional[str] = None
    dominant_weather: Optional[str] = None


class AdviceRequest(BaseModel):
    """Request for prescriptive advice and fertilizer recommendations"""
    user_id: str
    context: AdviceContext
    k: int = Field(4, ge=1, le=10, description="Number of knowledge references to retrieve")


class AdviceResponse(BaseModel):
    """Prescriptive advice with structured recommendations"""
    advice: str = Field(..., alias="advice")
    fertilizer_recommendations: List[str] = Field(default_factory=list, alias="fertilizerRecommendations")
    prioritized_actions: List[str] = Field(default_factory=list, alias="prioritizedActions")
    risk_warnings: List[str] = Field(default_factory=list, alias="riskWarnings")
    seed_recommendations: List[str] = Field(default_factory=list, alias="seedRecommendations")
    contexts: List[Dict[str, Any]] = Field(default_factory=list, alias="contexts")

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "examples": [
                {
                    "advice": "Narrative guidance...",
                    "fertilizerRecommendations": ["Use NPK 17-17-17 at planting", "Top-dress with CAN at V6"],
                    "prioritizedActions": ["Mulch fields", "Schedule irrigation"],
                    "riskWarnings": ["Low rainfall expected"],
                    "seedRecommendations": ["Use drought-tolerant hybrid H516"],
                    "contexts": []
                }
            ]
        }
    }
