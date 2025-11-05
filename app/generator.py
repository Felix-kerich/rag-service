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
    
    # Configure the client
    genai.configure(api_key=api_key)
    self.model = genai.GenerativeModel(self.model_name)

  def _is_greeting(self, question: str) -> bool:
    q = (question or "").strip().lower()
    if not q:
      return False
    # consider short messages with greeting tokens as greetings
    tokens = {t.strip(".,!? ") for t in q.split()}
    return any(t in tokens for t in GREETING_TOKENS) and len(tokens) <= 6

  def generate(self, question: str, contexts: List[str]) -> str:
    if self._is_greeting(question):
      return "Hello! How can I help you with maize farming today?"

    # --- Prompt Construction ---
    if contexts:
      context_block = "\n\n".join([f"Source {i+1}:\n{c}" for i, c in enumerate(contexts)])
      prompt = (
        "You are a friendly, concise agronomy assistant for maize farmers in Kenya. "
        "Only answer questions related to maize farming (e.g., planting, varieties, soil, fertilizer, pests, diseases, irrigation, harvest, storage, markets). "
        "If the user asks about anything outside maize farming, politely refuse with a short note: 'Sorry, I can only help with maize farming topics.' and invite a maize-related question. "
        "Use ONLY the provided sources to answer. If unsure or sources conflict, say so and suggest next steps. "
        "Keep responses short and actionable, use bullet points when useful, and keep a warm tone.\n\n"
        f"Question: {question}\n\nSources:\n{context_block}\n\nAnswer:"
      )
    else:
      prompt = (
        "You are a friendly, concise agronomy assistant for maize farmers in Kenya. "
        "Only answer questions related to maize farming. If the question is outside maize farming, reply: 'Sorry, I can only help with maize farming topics.' and invite a maize-related question. "
        "If you lack enough information, say so and ask for specifics.\n\n"
        f"Question: {question}\n\nAnswer:"
      )
    # --- End Prompt Construction ---


    try:
      # Call the model
      resp = self.model.generate_content(prompt, generation_config={
        "temperature": 0.2,
        "max_output_tokens": 400
      })

      # Attempt to get the text
      text = resp.text
      
      # An additional check if the text is empty but the accessor didn't raise
      if not text:
          finish_reason = resp.candidates[0].finish_reason if resp.candidates else None
          if finish_reason == 2:
              return (
                  "Sorry, the response for that query was blocked by safety filters. "
                  "Please try rephrasing your question about maize farming."
              )
          return "I'm sorry, I couldn't generate a response. Please check your context documents and try again."
          
      return text.strip()

    # ✅ FIX: Handle the ValueError specifically for empty response/safety blocks
    except ValueError as e:
      # This block catches the exact error from resp.text when content is empty (Finish Reason 2)
      if "finish_reason" in str(e) and "2" in str(e):
          return (
              "Sorry, the content for that query was blocked by safety filters (Finish Reason 2). "
              "Please try rephrasing your question about maize farming."
          )
      
      return f"An issue occurred while processing the model's response: {str(e)[:100]}"
    
    # Handle Network/API Errors
    except google_exceptions.GoogleAPIError as e:
      # Catch specific Google Generative AI API errors (e.g., rate limit, invalid key, etc.)
      return f"A Gemini API error occurred: {e}. Please check your GOOGLE_API_KEY and network connection."
    
    # Catch All Other Errors
    except Exception as e:
      # General fallback error handling
      return f"An unexpected error occurred: {str(e)[:200]}. The server may be unstable."