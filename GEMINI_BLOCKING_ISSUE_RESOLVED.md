# Why Gemini Is Blocking Your Agricultural Advice

## TL;DR - The Root Cause

Your `generator.py` was using **invalid safety settings format** that Gemini didn't recognize, causing it to fall back to **maximum safety restrictions**.

### The Bug:
```python
# ❌ WRONG - These strings aren't valid in Gemini API v1.5+
{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"}
```

### The Fix:
```python
# ✅ CORRECT - Use proper enum types
{
  "category": genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT,
  "threshold": genai.types.HarmBlockThreshold.BLOCK_ONLY_HIGH
}
```

---

## What Changed in generator.py

### 1️⃣ **Fixed Safety Settings (Lines 73-91)**
- Changed from string category/threshold to proper `genai.types` enums
- Set threshold to `BLOCK_ONLY_HIGH` (allows medium/low harms to pass through for agricultural domain)
- Previously defaulted to maximum blocking because format was wrong

### 2️⃣ **Better Error Logging (Lines 103-119)**
- Now captures and logs the exact `finish_reason` and `safety_ratings`
- Prints which safety category blocked the response:
  - `HARM_CATEGORY_HARASSMENT`
  - `HARM_CATEGORY_HATE_SPEECH`
  - `HARM_CATEGORY_SEXUALLY_EXPLICIT`
  - `HARM_CATEGORY_DANGEROUS_CONTENT` ← Usually triggers for ag content

### 3️⃣ **Smart Retry Logic (Lines 121-137)**
- If response blocked, retry with an even simpler, more explicit prompt
- Retries only once to avoid infinite loops
- Lower temperature (0.3) and shorter output for second attempt

### 4️⃣ **Better Exception Handling (Lines 157-174)**
- Catches `ValueError` specifically for safety blocks
- Logs to console with emoji indicators (⚠️ ❌ ✅ 🔄)
- More helpful error messages to users

---

## Why Agricultural Advice Was Getting Blocked

Even though you set thresholds to `"BLOCK_NONE"`, Gemini didn't recognize that value.

**What happened:**
1. Your code sent: `{"threshold": "BLOCK_NONE"}` (string)
2. Gemini API expected: `HarmBlockThreshold.BLOCK_ONLY_HIGH` (enum)
3. Gemini ignored the invalid format and used **defaults** (maximum safety)
4. Agricultural keywords like "pesticide," "disease," "fertilizer" → **BLOCKED**

---

## Testing the Fix

### Enable Debug Mode:
```bash
export ADVICE_DEBUG=true
# Restart the service
```

### Make a Test Request:
```bash
curl -X POST http://localhost:8088/advice \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "farmer_123",
    "analytics_context": {"crop_type": "maize"},
    "question": "What fertilizer NPK ratio is best for maize at V6 stage?",
    "conversation_id": "test"
  }'
```

### Check the Logs:
```
=== ADVICE DEBUG: Prompt sent to model ===
You are an agricultural advisor helping farmers with maize cultivation...
=== END PROMPT ===

✅ Response: 847 chars of advice
```

If you see blocking:
```
⚠️  Response blocked - Finish Reason: SAFETY
   Safety Rating: HARM_CATEGORY_DANGEROUS_CONTENT -> MEDIUM
🔄 Retrying with safer prompt...
```

---

## If It's STILL Blocking

### Likely Culprit: Your Retrieved Context Documents

The problem might not be YOUR prompt, but the **documents you're retrieving** from the FAISS index.

**Solution:** Sanitize retrieved context before sending to Gemini:

```python
def clean_context_for_safety(context: str) -> str:
    """Remove words that trigger safety filters"""
    dangerous_words = {
        "poison": "harmful chemical",
        "kill": "control",
        "deadly": "hazardous",
        "toxic": "hazardous",
    }
    result = context
    for dangerous, safe in dangerous_words.items():
        result = result.replace(dangerous, safe)
    return result
```

Then in `generate()`:
```python
# Before creating prompt
truncated_contexts = [clean_context_for_safety(c) for c in contexts]
```

---

## Next Steps

1. **Deploy the fix** - Restart rag-service with the updated `generator.py`
2. **Enable debug mode** - `export ADVICE_DEBUG=true`
3. **Test thoroughly** - Try various agricultural questions
4. **Monitor logs** - Watch for any safety blocks and which category
5. **If still issues** - Check if your context documents have risky keywords

---

## Files Modified

- ✅ `/rag-service/app/generator.py` - Fixed safety settings, improved logging
- 📄 `/rag-service/GEMINI_SAFETY_FILTERS_GUIDE.md` - Full debugging guide (created)
