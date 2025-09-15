import os
import json
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import orjson
from pypdf import PdfReader

from .retriever import Retriever
from .generator import Generator

load_dotenv()

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
GENERATION_MODEL = os.getenv("GENERATION_MODEL", "gemini-1.5-flash")
INDEX_DIR = os.getenv("INDEX_DIR", "data")

app = FastAPI(title="Maize RAG Service (Ollama + Gemini)", version="1.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

retriever = Retriever(embedding_model_name=EMBEDDING_MODEL, index_dir=INDEX_DIR)
generator = Generator(model_name=GENERATION_MODEL)


class Document(BaseModel):
  id: Optional[str] = None
  text: str
  metadata: Optional[Dict[str, Any]] = None

class IngestRequest(BaseModel):
  documents: List[Document]

class QueryRequest(BaseModel):
  question: str
  k: int = 4

@app.get("/health")
def health():
  return {"status": "ok"}

@app.post("/ingest")
def ingest(req: IngestRequest):
  retriever.add_documents([d.model_dump() for d in req.documents])
  retriever.persist()
  return {"status": "ok", "count": len(req.documents)}

@app.post("/ingest/files")
async def ingest_files(files: List[UploadFile] = File(...)):
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
      docs.append({"id": f.filename, "text": text, "metadata": {"filename": f.filename, "type": "pdf"}})
    else:
      text = raw.decode("utf-8", errors="ignore")
      docs.append({"id": f.filename, "text": text, "metadata": {"filename": f.filename, "type": "text"}})
  retriever.add_documents(docs)
  retriever.persist()
  return {"status": "ok", "count": len(docs)}

@app.post("/query")
def query(req: QueryRequest):
  results = retriever.search(req.question, k=req.k)
  answer = generator.generate(
    question=req.question,
    contexts=[r["text"] for r in results]
  )
  return {
    "answer": answer,
    "contexts": results
  } 