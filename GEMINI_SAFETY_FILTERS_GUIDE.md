# Gemini Safety Filters - Troubleshooting Guide

## Why Your Responses Are Getting Blocked

Gemini's safety filters may block agricultural advice for several reasons:

### Common Triggers:
1. **Pesticide/Chemical Keywords** - Words like "poison," "kill," "toxic" trigger DANGEROUS_CONTENT filter
2. **Disease Names** - "aflatoxin," specific crop diseases can trigger safety blocks
3. **Fertilizer Descriptions** - Detailed chemical compositions or application methods
4. **Economic Pressure Language** - If prompt sounds desperate or high-stakes
5. **Context Documents** - Retrieved documents with unfiltered keywords can trigger blocks

---

## What Was Fixed in `generator.py`

### ✅ **Before (Broken):**
```python
safety_settings = [
  {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},  # ❌ Wrong format
  {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
  # ...
]
```
**Problem:** String values like `"BLOCK_NONE"` aren't recognized by the Gemini API v1.5+. They default to strict blocking.

### ✅ **After (Fixed):**
```python
safety_settings = [
  {
    "category": genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT,
    "threshold": genai.types.HarmBlockThreshold.BLOCK_ONLY_HIGH  # ✅ Correct enum
  },
  # ...
]
```
**Improvement:** Uses proper enum values that Gemini recognizes. `BLOCK_ONLY_HIGH` = only block high-probability harms.

### ✅ **Threshold Levels Explained:**
- `BLOCK_NONE` - No blocking (not available in all versions)
- `BLOCK_ONLY_HIGH` - Only block extreme/definite harms ✅ **RECOMMENDED for ag domain**
- `BLOCK_MEDIUM_AND_ABOVE` - Block medium and above
- `BLOCK_LOW_AND_ABOVE` - Block anything, even low probability (too strict)

---

## How to Debug Further

### Enable Debug Mode:
```bash
export ADVICE_DEBUG=true
# Restart your service
```

This will log:
- ✅ Exact prompt sent to Gemini
- ✅ Finish reason code and safety ratings
- ✅ Whether retries succeeded
- ✅ Full error stack traces

### Example Debug Output:
```
⚠️  Response blocked - Finish Reason: 2
   Safety Rating: HARM_CATEGORY_DANGEROUS_CONTENT -> MEDIUM

🔄 Retrying with safer prompt...
✅ Retry succeeded: 847 chars
```

---

## Strategies to Prevent Blocking

### 1. **Clean Your Context Documents**
Remove or sanitize retrieved documents before sending to Gemini:

```python
def sanitize_context(ctx: str) -> str:
    """Remove trigger words from context"""
    replacements = {
        "poison": "harmful substance",
        "kill": "eliminate",
        "toxic": "hazardous",
        "pesticide": "crop protection agent"
    }
    result = ctx
    for old, new in replacements.items():
        result = result.replace(old, new)
    return result
```

### 2. **Use Domain-Specific Jargon**
Instead of:
- ❌ "How to poison weeds?"
- ✅ "What herbicides are effective against Striga?"

Instead of:
- ❌ "Kill the disease"
- ✅ "Manage early blight infection"

### 3. **Warm Up Your Prompts**
Add explicit context upfront:

```python
prompt = (
    "You are a licensed agricultural extension officer providing expert advice. "
    "This conversation is for legitimate farm management only. "
    "Question: {question}"
)
```

### 4. **Temperature & Token Tuning**
Lower temperature (more deterministic) can help:
```python
generation_config={
    "temperature": 0.3,  # Lower = more predictable, fewer edge cases
    "max_output_tokens": 500,  # Shorter responses less likely to trigger filters
}
```

---

## If Blocks Still Occur

### Option A: Use a Less Restricted Model
```python
# Try Gemini 2.0 if available (may have different safety defaults)
self.model = genai.GenerativeModel("gemini-2.0-flash")
```

### Option B: Implement Multi-Model Fallback
```python
try:
    # Try primary model
    response = gemini_model.generate_content(prompt)
except ValueError as e:
    if "safety" in str(e).lower():
        # Fall back to unfiltered local model or different provider
        response = open_source_model.generate_content(prompt)
```

### Option C: Pre-filter User Input
```python
def is_risky_question(question: str) -> bool:
    risky_words = {"poison", "kill", "destroy", "dangerous"}
    return any(w in question.lower() for w in risky_words)

if is_risky_question(user_question):
    return "Please rephrase your question to be more specific..."
```

---

## Testing Your Fix

### Quick Test:
```bash
curl -X POST http://localhost:8088/advice \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "analytics_context": {"crop_type": "maize"},
    "question": "What fertilizer should I use for maize?",
    "conversation_id": "test_conv"
  }'
```

### Expected Response:
- ✅ Legitimate maize advice (not blocked)
- ✅ If blocked initially, retry should succeed
- ✅ Debug logs show safety ratings

---

## References
- [Gemini Safety Settings Docs](https://ai.google.dev/docs/safety_settings)
- [HarmBlockThreshold Enum](https://ai.google.dev/api/rest/v1beta/HarmBlockThreshold)
- [Common Safety Filter Triggers](https://ai.google.dev/docs/safety_recommendations)

---

## Changes Summary

**File:** `/rag-service/app/generator.py`

| Change | Reason |
|--------|--------|
| Fixed safety settings enum format | Old string format wasn't recognized |
| Changed threshold to `BLOCK_ONLY_HIGH` | Allows legitimate ag content through |
| Added safety rating logging | See exactly why blocks occur |
| Implemented smart retry with simplified prompt | Recover from false positives |
| Better error messages | Users know why they can't get advice |

**To apply immediately:**
1. Restart your rag-service with `ADVICE_DEBUG=true`
2. Test with a farming question
3. Check logs for safety ratings
4. If still blocking, contact support with the logged safety category
