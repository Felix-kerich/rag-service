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
          "temperature": 0.7,  # Slightly lower for more consistent advice
          "max_output_tokens": 2000,  # Increased for detailed advice
          "top_p": 0.9,
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
  
  def generate_advice(self, analytics_context: str, enhanced_prompt: str, contexts: List[str]) -> str:
    """Specialized method for generating agricultural advice based on analytics"""
    
    if contexts:
      truncated_contexts = []
      for ctx in contexts[:5]:
        truncated_ctx = ctx[:2000] if len(ctx) > 2000 else ctx
        truncated_contexts.append(truncated_ctx)
      
      context_block = "\n\n".join([f"Knowledge Source {i+1}:\n{c}" for i, c in enumerate(truncated_contexts)])
      
      prompt = f"""You are an expert agricultural advisor specializing in maize farming with deep knowledge of East African farming conditions.

FARM ANALYTICS DATA:
{analytics_context}

KNOWLEDGE BASE REFERENCES:
{context_block}

TASK:
{enhanced_prompt}

IMPORTANT: Your response must be valid JSON only, without any markdown formatting or code blocks."""
    else:
      prompt = f"""You are an expert agricultural advisor specializing in maize farming with deep knowledge of East African farming conditions.

FARM ANALYTICS DATA:
{analytics_context}

TASK:
{enhanced_prompt}

IMPORTANT: Your response must be valid JSON only, without any markdown formatting or code blocks."""

    if self.debug:
      print(f"\n=== ADVICE PROMPT ===\n{prompt[:500]}...\n=== END ===\n")

    try:
      resp = self.model.generate_content(
        prompt,
        generation_config={
          "temperature": 0.6,  # Lower temperature for more consistent advice format
          "max_output_tokens": 2500,  # More tokens for comprehensive advice
          "top_p": 0.85,
          "top_k": 30
        },
        safety_settings=[]
      )

      text = resp.text
      if text and text.strip():
        return text.strip()
      
      # Fallback advice if generation fails
      return '{"advice": "Based on your farm data, focus on optimizing input costs while maintaining yield quality. Implement precision farming techniques and monitor soil health regularly.", "fertilizer_recommendations": ["Apply balanced NPK fertilizer at planting", "Top-dress with nitrogen at V6 stage"], "prioritized_actions": ["Conduct soil testing", "Optimize planting density", "Implement integrated pest management"], "risk_warnings": ["Monitor weather patterns for planting decisions", "Watch for pest and disease pressure"], "seed_recommendations": ["Use certified hybrid varieties adapted to your region"]}'

    except ValueError as e:
      print(f"⚠️  Advice Generation Error: {str(e)[:80]}")
      return '{"advice": "I encountered an issue generating specific advice. Please implement standard maize farming best practices and consult local agricultural extension services.", "fertilizer_recommendations": ["Apply recommended NPK rates for your soil type"], "prioritized_actions": ["Follow local planting calendar", "Monitor crop development stages"], "risk_warnings": ["Stay updated on weather forecasts", "Scout fields regularly"], "seed_recommendations": ["Use locally adapted varieties"]}'
    
    except google_exceptions.GoogleAPIError as e:
      print(f"⚠️  API Error in Advice Generation: {str(e)[:80]}")
      return '{"advice": "Unable to generate personalized advice at this time. Focus on maintaining good agricultural practices and seek guidance from local experts.", "fertilizer_recommendations": ["Follow standard fertilization schedule"], "prioritized_actions": ["Maintain field records", "Follow crop calendar"], "risk_warnings": ["Monitor for common pests and diseases"], "seed_recommendations": ["Use quality certified seeds"]}'
    
    except Exception as e:
      print(f"⚠️  Unexpected error in advice generation: {str(e)[:80]}")
      return '{"advice": "Technical issue encountered. Please try again or consult agricultural extension services for guidance.", "fertilizer_recommendations": ["Apply standard fertilizer recommendations"], "prioritized_actions": ["Follow best farming practices"], "risk_warnings": ["Monitor crop health regularly"], "seed_recommendations": ["Use recommended seed varieties"]}'
