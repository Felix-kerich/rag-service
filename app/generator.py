import os
from typing import List

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions


GREETING_TOKENS = {"hi", "hii", "hello", "hey", "habari", "mambo", "salama", "niaje", "sup"}


class Generator:
  def __init__(self, model_name: str = "gemini-1.5-flash"):
    self.model_name = model_name
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
      raise RuntimeError("GOOGLE_API_KEY is not set. Please export it in your environment.")
    
    genai.configure(api_key=api_key)
    self.model = genai.GenerativeModel(self.model_name)
    self.debug = os.getenv("ADVICE_DEBUG", "false").lower() == "true"

  def _is_greeting(self, question: str) -> bool:
    q = (question or "").strip().lower()
    if not q:
      return False
    tokens = {t.strip(".,!? ") for t in q.split()}
    return any(t in tokens for t in GREETING_TOKENS) and len(tokens) <= 6

  def generate(self, question: str, contexts: List[str]) -> str:
    if self._is_greeting(question):
      return "Hello! How can I help you with maize farming today?"

    if contexts:
      truncated_contexts = []
      for ctx in contexts[:5]:
        truncated_ctx = ctx[:1500] if len(ctx) > 1500 else ctx
        truncated_contexts.append(truncated_ctx)
      
      context_block = "\n\n".join([f"Source {i+1}:\n{c}" for i, c in enumerate(truncated_contexts)])
      prompt = f"Based on these materials, answer: {question}\n\nReference Materials:\n{context_block}\n\nYour Response:"
    else:
      prompt = f"Answer this farming question: {question}\n\nYour Response:"

    if self.debug:
      print(f"\n=== PROMPT ===\n{prompt[:300]}...\n=== END ===\n")

    try:
      resp = self.model.generate_content(
        prompt,
        generation_config={
          "temperature": 0.8,
          "max_output_tokens": 1500,
          "top_p": 0.95,
          "top_k": 40
        },
        safety_settings=[]
      )

      text = resp.text
      if text and text.strip():
        return text.strip()
      
      return f"For your question on {question}, here are practical recommendations: Review your farm records, apply proven techniques, and monitor results closely. Consult local agricultural experts for additional guidance specific to your location and conditions."

    except ValueError as e:
      print(f"⚠️  Error: {str(e)[:80]}")
      return f"Regarding your farming question: Please implement standard best practices for your crops, maintain detailed records, and seek guidance from local agricultural extension services."
    
    except google_exceptions.GoogleAPIError as e:
      print(f"⚠️  API Error: {str(e)[:80]}")
      return "Please try your question again or contact local agricultural services for guidance."
    
    except Exception as e:
      print(f"⚠️  Unexpected error: {str(e)[:80]}")
      return "I'm having a temporary issue. Please try again or contact local agricultural services."
