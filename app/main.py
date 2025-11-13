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
    HealthResponse,
    AdviceRequest,
    AdviceResponse
)
from .models import Conversation, ConversationSummary
import logging

load_dotenv()

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
GENERATION_MODEL = os.getenv("GENERATION_MODEL", "gemini-2.5-flash")
INDEX_DIR = os.getenv("INDEX_DIR", "data")
CONVERSATION_DIR = os.getenv("CONVERSATION_DIR", "data/conversations")
PORT = int(os.getenv("PORT", "8088"))
ADVICE_DEBUG = os.getenv("ADVICE_DEBUG", "false").lower() == "true"

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


def _format_analytics_context(ctx: dict) -> str:
    # Create a compact, readable context block for prompting
    lines = []
    lines.append(f"Crop Type: {ctx.get('crop_type')}")
    if ctx.get("period_start") or ctx.get("period_end"):
        lines.append(f"Period: {ctx.get('period_start')} to {ctx.get('period_end')}")
    for field in [
        "total_expenses","total_revenue","net_profit","profit_margin",
        "total_yield","average_yield_per_unit","best_yield","worst_yield"
    ]:
        if ctx.get(field) is not None:
            lines.append(f"{field.replace('_',' ').title()}: {ctx.get(field)}")
    if ctx.get("soil_type") or ctx.get("soil_ph"):
        lines.append(f"Soil: type={ctx.get('soil_type')}, pH={ctx.get('soil_ph')}")
    if ctx.get("rainfall_mm"):
        lines.append(f"Rainfall (mm): {ctx.get('rainfall_mm')}")
    if ctx.get("location"):
        lines.append(f"Location: {ctx.get('location')}")
    if ctx.get("expenses_by_category"):
        lines.append("Expenses by Category:")
        for k,v in (ctx.get("expenses_by_category") or {}).items():
            lines.append(f"  - {k}: {v}")
    if ctx.get("expenses_by_growth_stage"):
        lines.append("Expenses by Growth Stage:")
        for k,v in (ctx.get("expenses_by_growth_stage") or {}).items():
            lines.append(f"  - {k}: {v}")
    return "\n".join(lines)


def _to_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clean_list(values: Any) -> List[str]:
    if not values:
        return []
    if isinstance(values, list):
        return [str(v).strip() for v in values if str(v).strip()]
    if isinstance(values, str):
        return [values.strip()] if values.strip() else []
    return []


def _dedupe(seq: List[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for item in seq:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def _decorate_advice(text: str) -> str:
    base = (text or "").strip()
    if not base:
        base = "Here is your latest farm performance summary and tailored guidance."
    greeting = "Hello Farmer,"
    lower = base.lower()
    if not lower.startswith(("hello", "hi ", "hi,", "dear", "greetings", "good morning", "good afternoon", "good evening")):
        base = f"{greeting}\n\n{base}"
    closing = "\n\nWishing you a productive season,\nShambaBora Agronomy Assistant"
    if "shambabora agronomy assistant" not in base.lower():
        base = base.rstrip() + closing
    return base


def _extract_structured_lists(answer: str) -> Dict[str, List[str]]:
    sections = {
        "fertilizer": [],
        "actions": [],
        "risks": [],
        "seeds": []
    }
    if not answer:
        return sections

    current = None
    for raw_line in answer.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        normalized = line.lower().rstrip(":")
        if "fertiliz" in normalized:
            current = "fertilizer"
            continue
        if "seed" in normalized and ("recommend" in normalized or "variet" in normalized):
            current = "seeds"
            continue
        if any(keyword in normalized for keyword in ("risk", "warning", "caution", "watch")):
            current = "risks"
            continue
        if any(keyword in normalized for keyword in ("action", "next step", "priority", "plan", "task")):
            current = "actions"
            continue

        bullet = line[0] in {"-", "*", "•"} or (line[:2].isdigit() and line[2:3] in {".", ")", ":"})
        if bullet:
            cleaned = line.lstrip("-*• \t0123456789.).").strip()
            if not cleaned:
                continue
            target = current or "actions"
            sections[target].append(cleaned)
        elif current and len(line.split()) <= 14:
            # Short emphatic sentences following a heading
            sections[current].append(line)

    return sections


def _structured_lists_empty(lists: Dict[str, List[str]]) -> bool:
    return not any(lists.values())


def _generate_structured_lists_with_model(ctx: Dict[str, Any], narrative: str) -> Dict[str, List[str]]:
    prompt = (
        "You are an agricultural advisor. Convert the analytics summary and narrative below into structured bullet lists. "
        "Return STRICT JSON with keys fertilizer_recommendations, prioritized_actions, risk_warnings, seed_recommendations. "
        "Each value must be a list of strings with rich, specific guidance.\n\n"
        f"Analytics Summary:\n{_format_analytics_context(ctx)}\n\n"
        f"Narrative Advice:\n{narrative}\n"
    )
    follow_up = generator.generate(prompt, [])
    try:
        start = follow_up.find("{")
        end = follow_up.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return {}
        parsed = json.loads(follow_up[start:end + 1])
        return {
            "fertilizer": _clean_list(parsed.get("fertilizer_recommendations")),
            "actions": _clean_list(parsed.get("prioritized_actions")),
            "risks": _clean_list(parsed.get("risk_warnings")),
            "seeds": _clean_list(parsed.get("seed_recommendations"))
        }
    except Exception:
        return {}


def _generate_rule_based_recommendations(ctx: Dict[str, Any]) -> Dict[str, Any]:
    crop = ctx.get("crop_type") or "the crop"
    advice_sections: List[str] = []
    prioritized_actions: List[str] = []
    fertilizer_recommendations: List[str] = []
    risk_warnings: List[str] = []
    seed_recommendations: List[str] = []

    profit_margin = _to_float(ctx.get("profit_margin"))
    net_profit = _to_float(ctx.get("net_profit"))
    total_expenses = _to_float(ctx.get("total_expenses"))
    total_revenue = _to_float(ctx.get("total_revenue"))
    avg_yield = _to_float(ctx.get("average_yield_per_unit"))
    best_yield = _to_float(ctx.get("best_yield"))
    worst_yield = _to_float(ctx.get("worst_yield"))
    rainfall = _to_float(ctx.get("rainfall_mm"))
    dominant_weather = (ctx.get("dominant_weather") or "").lower()
    soil_ph = _to_float(ctx.get("soil_ph"))
    location = ctx.get("location")
    expenses_by_category = ctx.get("expenses_by_category") or {}

    summary_parts: List[str] = []
    if total_revenue is not None:
        summary_parts.append(f"generated revenue of approximately {total_revenue:.2f}")
    if total_expenses is not None:
        summary_parts.append(f"spent about {total_expenses:.2f} in inputs")
    if net_profit is not None:
        summary_parts.append(f"resulted in net profit near {net_profit:.2f}")
    if summary_parts:
        advice_sections.append(
            f"In the recent period, your {crop} enterprise {' and '.join(summary_parts)}."
        )

    if avg_yield is not None and best_yield is not None:
        advice_sections.append(
            f"Average yield per unit sits at {avg_yield:.2f}, with best-performing plots reaching {best_yield:.2f}."
        )
    elif avg_yield is not None:
        advice_sections.append(f"Average yield per unit is {avg_yield:.2f}.")

    if profit_margin is not None:
        if profit_margin < 15:
            advice_sections.append("Profit margins are tight; focus on reducing input costs and improving yield efficiency.")
            prioritized_actions.append("Review major expense categories and negotiate bulk pricing for inputs.")
        elif profit_margin < 30:
            advice_sections.append("Margins are moderate; optimize fertilization and pest control to raise profitability.")
        else:
            advice_sections.append("Profit margins look strong—maintain cost discipline while scaling the practices that deliver the best results.")

    if net_profit is not None and net_profit < 0:
        advice_sections.append("Net profit is negative; prioritize high-impact interventions and pause low-return activities.")
        risk_warnings.append("Current season is operating at a loss; reassess selling prices and input expenses urgently.")

    if avg_yield and best_yield and best_yield - avg_yield > max(0.2 * avg_yield, 0.1):
        advice_sections.append("Top-performing fields are far outpacing the average. Audit their management and replicate those practices on weaker plots.")
        prioritized_actions.append("Document the management of your highest-yielding field and apply the same schedule to underperforming areas.")

    if worst_yield and avg_yield and worst_yield < 0.8 * avg_yield:
        risk_warnings.append("Some plots are well below average yield; investigate soil fertility, pest pressure, or water stress.")

    fertilizer_recommendations.extend(_fertilizer_guidance(crop, soil_ph))
    seed_recommendations.extend(_seed_guidance(crop, location, rainfall))

    pesticide_cost = expenses_by_category.get("PESTICIDES")
    fertilizer_cost = expenses_by_category.get("FERTILIZER")
    if pesticide_cost and fertilizer_cost:
        try:
            pesticide_cost = float(pesticide_cost)
            fertilizer_cost = float(fertilizer_cost)
            if pesticide_cost > fertilizer_cost * 0.5:
                advice_sections.append("Pesticide spending is high. Deploy integrated pest management to cut chemical dependence.")
                prioritized_actions.append("Scout fields weekly and use targeted biological controls to lower pesticide costs.")
        except (TypeError, ValueError):
            pass

    if rainfall is not None:
        if rainfall < 350:
            advice_sections.append("Rainfall is below ideal levels; concentrate on moisture conservation and supplemental irrigation.")
            prioritized_actions.append("Apply mulch and schedule irrigation around critical growth stages.")
            risk_warnings.append("Low rainfall increases drought stress risk; monitor soil moisture closely.")
        elif rainfall < 500:
            advice_sections.append("Rainfall is moderately low; focus on drought-tolerant varieties and timely weeding to reduce moisture competition.")
        elif rainfall > 800:
            advice_sections.append("High rainfall can lead to nutrient leaching; adjust fertilization to compensate for losses.")
            risk_warnings.append("Excess rainfall raises disease risk; tighten your crop protection schedule.")
            prioritized_actions.append("Improve drainage around low-lying fields to avoid waterlogging.")

    if dominant_weather:
        if "dry" in dominant_weather or "drought" in dominant_weather:
            advice_sections.append("Weather outlook indicates dry spells; schedule irrigation shifts early mornings and late evenings.")
            risk_warnings.append("Extended dry periods increase risk of silk desiccation; maintain soil moisture during tasseling.")
            prioritized_actions.append("Install soil moisture sensors or manual probes to trigger irrigation before wilting.")
        if "wet" in dominant_weather or "rain" in dominant_weather:
            advice_sections.append("Expect wetter conditions; scout for fungal diseases weekly and rotate fungicides to prevent resistance.")
            risk_warnings.append("Persistent moisture favours leaf blights and rust; keep protective sprays ready.")
        if "wind" in dominant_weather or "storm" in dominant_weather:
            risk_warnings.append("High winds can cause lodging; consider staking or strategic windbreaks near exposed fields.")

    if total_expenses and total_revenue and total_expenses > total_revenue:
        risk_warnings.append("Expenses exceed revenue for this period; prioritize profitable crops and defer non-essential purchases.")

    if not prioritized_actions:
        prioritized_actions.append("Keep detailed records of field activities and yields to fine-tune next season’s plan.")

    if not fertilizer_recommendations:
        fertilizer_recommendations.append("Apply a balanced N-P-K fertilizer at planting and supplement with nitrogen at knee-high stage.")
    if not seed_recommendations:
        seed_recommendations.append(f"Select certified, drought-resilient hybrid seed suitable for {crop}, such as H516 or DK8031.")
    prioritized_actions.append("Harvest at physiological maturity and dry maize to 13% moisture before storage.")

    storage_tip = "Dry shelled maize thoroughly and store in airtight hermetic bags or silos to prevent aflatoxin buildup."
    if storage_tip not in risk_warnings:
        risk_warnings.append(storage_tip)

    fertilizer_recommendations = _dedupe(fertilizer_recommendations)
    prioritized_actions = _dedupe(prioritized_actions)
    risk_warnings = _dedupe(risk_warnings)
    seed_recommendations = _dedupe(seed_recommendations)

    advice_text = " ".join(advice_sections) if advice_sections else f"Continue refining your {crop} management with careful record keeping and timely field operations."
    return {
        "advice": advice_text,
        "fertilizer_recommendations": fertilizer_recommendations,
        "prioritized_actions": prioritized_actions,
        "risk_warnings": risk_warnings if risk_warnings else ["Continue monitoring crop health and market prices each week."],
        "seed_recommendations": seed_recommendations
    }


def _fertilizer_guidance(crop: str, soil_ph: Optional[float]) -> List[str]:
    recs: List[str] = []
    crop_name = crop or "your crop"
    if soil_ph is None:
        recs.append(f"For {crop_name}, apply a basal NPK (17-17-17 or 23-23-0) at planting and top-dress with CAN or urea at knee height and tasseling.")
    elif soil_ph < 5.5:
        recs.append("Soil pH is acidic; apply agricultural lime before the next season to raise pH above 5.8.")
        recs.append(f"Use a high-phosphorus starter (DAP or 10-26-26) for {crop_name}, then top-dress with CAN or urea once rainfall is stable.")
    elif 5.5 <= soil_ph <= 6.5:
        recs.append(f"Soil pH is optimal; use a balanced NPK at planting and follow with nitrogen top-dressing at V6 and pre-tassel stages.")
    else:
        recs.append("Soil pH is alkaline; incorporate elemental sulfur or acidifying organic matter to move pH toward 6.2.")
        recs.append(f"Supplement with foliar micronutrients (zinc, boron) to support {crop_name} under high pH conditions.")
    return recs


def _seed_guidance(crop: str, location: Optional[str], rainfall: Optional[float]) -> List[str]:
    crop_name = crop or "your crop"
    regional_hint = f" for {location}" if location else ""
    recs: List[str] = []
    if rainfall is not None and rainfall < 400:
        recs.append(f"Choose early-maturing, drought-tolerant hybrids{regional_hint} such as DUMA 43, DK8031, or PIONEER P2859.")
    elif rainfall is not None and rainfall > 700:
        recs.append(f"Opt for high-yield, disease-tolerant hybrids{regional_hint} like H629 or PIONEER P3812 that perform well in wetter zones.")
    else:
        recs.append(f"Use certified hybrid seed{regional_hint}, e.g., H614D or SC DUMA 43, and treat seed with a systemic fungicide/insecticide before planting.")
    return recs


@app.post("/advice", response_model=AdviceResponse, tags=["Advisory"])
def advice(req: AdviceRequest):
    """
    Generate prescriptive advice and fertilizer recommendations using provided analytics context.
    """
    ctx_dict = req.context.model_dump()
    analytics_block = _format_analytics_context(ctx_dict)

    question = (
        "Given the farm analytics below, provide prescriptive, step-by-step recommendations to improve yield and profitability. "
        "Recommend specific fertilizer types and application timings based on soil and crop stage, suggest cost optimizations, and highlight risks. "
        "Return your result as strict JSON with keys: advice (string), fertilizer_recommendations (string[]), prioritized_actions (string[]), risk_warnings (string[])."
    )

    # Retrieve context from knowledge base
    results = retriever.search(
        f"Best agronomic practices and fertilizer programs for {req.context.crop_type}. Soil={req.context.soil_type} pH={req.context.soil_ph}",
        k=req.k
    )

    # Build a single prompt including analytics
    prompt = (
        "You are an agricultural advisor for smallholder and commercial farmers.\n\n"
        "Farm Analytics:\n"
        f"{analytics_block}\n\n"
        "Task:\n"
        f"{question}\n"
        "Ensure JSON is valid and does not include markdown code fences."
    )

    answer = generator.generate(prompt, contexts=[r["text"] for r in results])
    if ADVICE_DEBUG:
        print("\n=== ADVICE DEBUG: Primary Model Answer ===")
        print(answer)
        print("=== END ANSWER ===\n")
    fallback_plan = _generate_rule_based_recommendations(ctx_dict)

    # Try to parse JSON from the model output
    parsed: Dict[str, Any] = {}
    try:
        # Heuristic: find first JSON object in the output
        start = answer.find("{")
        end = answer.rfind("}")
        if start != -1 and end != -1 and end > start:
            parsed = json.loads(answer[start:end+1])
            if ADVICE_DEBUG:
                print("=== ADVICE DEBUG: Parsed JSON keys from primary model ===")
                print(list(parsed.keys()))
                print("=== END PARSED ===\n")
    except Exception:
        parsed = {}

    def _extract_list(key: str) -> List[str]:
        v = parsed.get(key)
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()]
        # fallback: derive bullet points from text
        lines = []
        for line in answer.splitlines():
            s = line.strip()
            if s.startswith(("-", "*")) and len(s) > 2:
                lines.append(s.lstrip("-* ").strip())
        return lines[:6]

    if "blocked by safety filters" in answer.lower():
        decorated = _decorate_advice(fallback_plan["advice"])
        if ADVICE_DEBUG:
            print("=== ADVICE DEBUG: Safety filter triggered; returning fallback plan ===")
            print(fallback_plan)
            print("=== END FALLBACK ===\n")
        return AdviceResponse(
            advice=decorated,
            fertilizer_recommendations=_clean_list(fallback_plan["fertilizer_recommendations"]),
            prioritized_actions=_clean_list(fallback_plan["prioritized_actions"]),
            risk_warnings=_clean_list(fallback_plan["risk_warnings"]),
            seed_recommendations=_clean_list(fallback_plan["seed_recommendations"]),
            contexts=results
        )

    advice_text = parsed.get("advice")
    structured_lists = {
        "fertilizer": _clean_list(_extract_list("fertilizer_recommendations")),
        "actions": _clean_list(_extract_list("prioritized_actions")),
        "risks": _clean_list(_extract_list("risk_warnings")),
        "seeds": _clean_list(_extract_list("seed_recommendations"))
    }
    if ADVICE_DEBUG:
        print("=== ADVICE DEBUG: Initial structured lists from primary JSON ===")
        print(structured_lists)
        print("=== END LISTS ===\n")

    if not isinstance(advice_text, str) or not advice_text.strip():
        narrative = (answer or "").strip()
        if not narrative:
            decorated = _decorate_advice(fallback_plan["advice"])
            if ADVICE_DEBUG:
                print("=== ADVICE DEBUG: Empty narrative; using fallback plan ===")
                print(fallback_plan)
                print("=== END FALLBACK ===\n")
            return AdviceResponse(
                advice=decorated,
                fertilizer_recommendations=_clean_list(fallback_plan["fertilizer_recommendations"]),
                prioritized_actions=_clean_list(fallback_plan["prioritized_actions"]),
                risk_warnings=_clean_list(fallback_plan["risk_warnings"]),
                seed_recommendations=_clean_list(fallback_plan["seed_recommendations"]),
                contexts=results
            )
        advice_text = narrative
        structured_lists = _extract_structured_lists(narrative)
        if ADVICE_DEBUG:
            print("=== ADVICE DEBUG: Heuristic lists extracted from narrative ===")
            print(structured_lists)
            print("=== END HEURISTIC ===\n")
        if _structured_lists_empty(structured_lists):
            generated_lists = _generate_structured_lists_with_model(ctx_dict, narrative)
            if generated_lists:
                structured_lists = generated_lists
                if ADVICE_DEBUG:
                    print("=== ADVICE DEBUG: Generated lists via follow-up model JSON ===")
                    print(structured_lists)
                    print("=== END FOLLOW-UP ===\n")
    else:
        # parsed JSON but still missing lists; ask model if needed
        if _structured_lists_empty(structured_lists):
            generated_lists = _generate_structured_lists_with_model(ctx_dict, advice_text)
            if generated_lists:
                structured_lists = generated_lists
                if ADVICE_DEBUG:
                    print("=== ADVICE DEBUG: Filled missing lists via follow-up model JSON ===")
                    print(structured_lists)
                    print("=== END FOLLOW-UP ===\n")

    advice_text = _decorate_advice(advice_text)

    return AdviceResponse(
        advice=advice_text.strip(),
        fertilizer_recommendations=structured_lists["fertilizer"],
        prioritized_actions=structured_lists["actions"],
        risk_warnings=structured_lists["risks"],
        seed_recommendations=structured_lists["seeds"],
        contexts=results
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