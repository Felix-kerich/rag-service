import os
import json
from typing import List, Dict, Any

import faiss
import numpy as np
import ollama


def _l2_normalize(vectors: np.ndarray) -> np.ndarray:
  norms = np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-12
  return vectors / norms


class Retriever:
  def __init__(self, embedding_model_name: str = "nomic-embed-text", index_dir: str = "data"):
    self.embedding_model_name = embedding_model_name
    self.index_dir = index_dir
    self.index_path = os.path.join(index_dir, "index.faiss")
    self.meta_path = os.path.join(index_dir, "meta.json")

    os.makedirs(index_dir, exist_ok=True)

    self.index = None
    self.metadata: List[Dict[str, Any]] = []

    if os.path.exists(self.index_path) and os.path.exists(self.meta_path):
      self.index = faiss.read_index(self.index_path)
      with open(self.meta_path, "r", encoding="utf-8") as f:
        self.metadata = json.load(f)

  def _embed(self, texts: List[str]) -> np.ndarray:
    vectors: List[List[float]] = []
    for t in texts:
      resp = ollama.embeddings(model=self.embedding_model_name, prompt=t)
      vectors.append(resp["embedding"])  # type: ignore
    arr = np.array(vectors, dtype=np.float32)
    return _l2_normalize(arr)

  def _ensure_index(self, dim: int):
    if self.index is None:
      self.index = faiss.IndexFlatIP(dim)

  def add_documents(self, docs: List[Dict[str, Any]]):
    if not docs:
      return
    texts = [d.get("text", "") for d in docs]
    vectors = self._embed(texts)
    self._ensure_index(vectors.shape[1])
    self.index.add(vectors)
    self.metadata.extend(docs)

  def persist(self):
    if self.index is None:
      return
    faiss.write_index(self.index, self.index_path)
    with open(self.meta_path, "w", encoding="utf-8") as f:
      json.dump(self.metadata, f, ensure_ascii=False)

  def search(self, query: str, k: int = 4) -> List[Dict[str, Any]]:
    if self.index is None or self.index.ntotal == 0:
      return []
    q = self._embed([query])
    scores, idxs = self.index.search(q, min(k, self.index.ntotal))
    results: List[Dict[str, Any]] = []
    for score, idx in zip(scores[0], idxs[0]):
      if idx == -1:
        continue
      doc = self.metadata[idx]
      results.append({"score": float(score), **doc})
    return results 