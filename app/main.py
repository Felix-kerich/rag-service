import os
import json
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import orjson
from pypdf import PdfReader

from .retriever import Retriever
from .generator import Generator
from .database import ConversationDatabase
from .schemas import (
    IngestRequest, 
    QueryRequest, 
    QueryResponse, 
    CreateConversationRequest,
    UpdateConversationRequest,
    HealthResponse
)
from .models import Conversation, ConversationSummary

load_dotenv()

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
GENERATION_MODEL = os.getenv("GENERATION_MODEL", "gemini-1.5-flash")
INDEX_DIR = os.getenv("INDEX_DIR", "data")
CONVERSATION_DIR = os.getenv("CONVERSATION_DIR", "data/conversations")
PORT = int(os.getenv("PORT", "8088"))

app = FastAPI(
    title="Professional Maize RAG Service",
    description="AI-powered agricultural advisory service with conversation history",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
retriever = Retriever(embedding_model_name=EMBEDDING_MODEL, index_dir=INDEX_DIR)
generator = Generator(model_name=GENERATION_MODEL)
conversation_db = ConversationDatabase(db_dir=CONVERSATION_DIR)

@app.get("/health", response_model=HealthResponse, tags=["System"])
def health():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        timestamp=datetime.utcnow().isoformat(),
        services={
            "retriever": "operational",
            "generator": "operational",
            "database": "operational"
        }
    )

@app.post("/ingest", tags=["Document Management"])
def ingest(req: IngestRequest):
    """
    Ingest documents into the knowledge base
    
    - **documents**: List of documents with text and optional metadata
    """
    retriever.add_documents([d.model_dump() for d in req.documents])
    retriever.persist()
    return {
        "status": "success",
        "message": "Documents ingested successfully",
        "count": len(req.documents)
    }

@app.post("/ingest/files", tags=["Document Management"])
async def ingest_files(files: List[UploadFile] = File(...)):
    """
    Upload and ingest files (PDF or text) into the knowledge base
    
    - **files**: List of files to upload (supports PDF and text files)
    """
    docs: List[Dict[str, Any]] = []
    for f in files:
        raw = await f.read()
        name = (f.filename or "").lower()
        if name.endswith(".pdf"):
            # Parse PDF bytes
            from io import BytesIO
            reader = PdfReader(BytesIO(raw))
            pages_text: List[str] = []
            for page in reader.pages:
                pages_text.append(page.extract_text() or "")
            text = "\n\n".join(pages_text)
            docs.append({
                "id": f.filename, 
                "text": text, 
                "metadata": {"filename": f.filename, "type": "pdf"}
            })
        else:
            text = raw.decode("utf-8", errors="ignore")
            docs.append({
                "id": f.filename, 
                "text": text, 
                "metadata": {"filename": f.filename, "type": "text"}
            })
    
    retriever.add_documents(docs)
    retriever.persist()
    return {
        "status": "success",
        "message": "Files ingested successfully",
        "count": len(docs),
        "files": [f.filename for f in files]
    }

@app.post("/query", response_model=QueryResponse, tags=["Query"])
def query(req: QueryRequest):
    """
    Query the RAG system with conversation history support
    
    - **question**: The question to ask
    - **k**: Number of context documents to retrieve (1-10)
    - **conversation_id**: Optional conversation ID for history tracking
    - **user_id**: User identifier (required)
    """
    # Retrieve relevant contexts
    results = retriever.search(req.question, k=req.k)
    
    # Generate answer
    answer = generator.generate(
        question=req.question,
        contexts=[r["text"] for r in results]
    )
    
    # Handle conversation history
    conversation_id = req.conversation_id
    if not conversation_id:
        # Create new conversation if not provided
        conversation = conversation_db.create_conversation(
            user_id=req.user_id,
            title=req.question[:50] + ("..." if len(req.question) > 50 else "")
        )
        conversation_id = conversation.conversation_id
    
    # Add user message
    conversation_db.add_message(
        conversation_id=conversation_id,
        role="user",
        content=req.question
    )
    
    # Add assistant message with contexts
    conversation_db.add_message(
        conversation_id=conversation_id,
        role="assistant",
        content=answer,
        contexts=results
    )
    
    return QueryResponse(
        answer=answer,
        contexts=results,
        conversation_id=conversation_id
    )


# ==================== Conversation Management Endpoints ====================

@app.post("/conversations", response_model=Conversation, tags=["Conversations"])
def create_conversation(req: CreateConversationRequest):
    """
    Create a new conversation
    
    - **user_id**: User identifier
    - **title**: Optional conversation title
    - **metadata**: Optional metadata
    """
    conversation = conversation_db.create_conversation(
        user_id=req.user_id,
        title=req.title,
        metadata=req.metadata
    )
    return conversation


@app.get("/conversations/{conversation_id}", response_model=Conversation, tags=["Conversations"])
def get_conversation(conversation_id: str):
    """
    Get a specific conversation by ID
    
    - **conversation_id**: The conversation identifier
    """
    conversation = conversation_db.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@app.get("/users/{user_id}/conversations", response_model=List[ConversationSummary], tags=["Conversations"])
def get_user_conversations(
    user_id: str,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of conversations to return"),
    offset: int = Query(0, ge=0, description="Number of conversations to skip")
):
    """
    Get all conversations for a user
    
    - **user_id**: User identifier
    - **limit**: Maximum number of conversations to return (1-100)
    - **offset**: Number of conversations to skip for pagination
    """
    conversations = conversation_db.get_user_conversations(
        user_id=user_id,
        limit=limit,
        offset=offset
    )
    return conversations


@app.patch("/conversations/{conversation_id}", response_model=Conversation, tags=["Conversations"])
def update_conversation(conversation_id: str, req: UpdateConversationRequest):
    """
    Update conversation metadata
    
    - **conversation_id**: The conversation identifier
    - **title**: Optional new title
    - **metadata**: Optional new metadata
    """
    conversation = conversation_db.update_conversation(
        conversation_id=conversation_id,
        title=req.title,
        metadata=req.metadata
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@app.delete("/conversations/{conversation_id}", tags=["Conversations"])
def delete_conversation(conversation_id: str, user_id: str = Query(..., description="User ID for authorization")):
    """
    Delete a conversation
    
    - **conversation_id**: The conversation identifier
    - **user_id**: User identifier (for authorization)
    """
    success = conversation_db.delete_conversation(conversation_id, user_id)
    if not success:
        raise HTTPException(
            status_code=404, 
            detail="Conversation not found or unauthorized"
        )
    return {"status": "success", "message": "Conversation deleted successfully"} 