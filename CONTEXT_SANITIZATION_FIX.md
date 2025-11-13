# Context Document Sanitization - Safety Filter Fix v2

## Problem
Even with proper safety settings, Gemini was still blocking responses because the **retrieved context documents themselves** contained trigger words like:
- "poison/poisoning"
- "kill/killing"  
- "toxic/toxin"
- "death/dying"
- etc.

These words are common in agricultural PDFs but trigger safety filters when passed to Gemini.

---

## Solution Implemented

### 1. **Context Sanitization Function**
Added `sanitize_context_for_safety()` that replaces agricultural trigger words with safer alternatives:

```python
SAFETY_TRIGGER_WORDS = {
    "poison": "harmful substance",
    "poisons": "harmful substances",
    "toxic": "hazardous",
    "kill": "control",
    "deadly": "severe",
    "die": "wilt or decline",
    "death": "failure",
    # ... etc
}

def sanitize_context_for_safety(ctx: str) -> str:
  if not ctx:
    return ctx
  result = ctx.lower()
  for trigger, replacement in SAFETY_TRIGGER_WORDS.items():
    result = result.replace(trigger, replacement)
  return result
```

### 2. **Shorter Context Chunks**
Reduced context size from 900 chars → **600 chars**
- Shorter content = fewer trigger words
- Faster processing
- Still provides useful information

### 3. **Two-Tier Retry Strategy**

When response is blocked:
1. **Retry 1** - Remove contexts entirely, ask question with general knowledge
   - Temperature: 0.2 (very deterministic)
   - Max tokens: 300 (brief)
   - Same safety settings

2. **Retry 2** - If still blocked, use minimal safety settings (only dangerous_content)
   - Temperature: 0.15 (ultra-deterministic)
   - Max tokens: 250 (very brief)
   - Reduced from 4 categories to 1

This gives 3 chances to get valid advice!

---

## What Changed

| Component | Before | After |
|-----------|--------|-------|
| Context Length | 900 chars | 600 chars |
| Context Sanitization | ❌ None | ✅ Removes trigger words |
| Retries on Block | 1 attempt | 2 attempts |
| Retry Strategy | Generic safer prompt | Context removal → minimal settings |
| Temperature on Retry | 0.3 | 0.2 → 0.15 |

---

## Example Flow

### Scenario: Question triggers safety filter

```
1. FIRST ATTEMPT
   - Sends: Question + Sanitized Context (600 chars)
   - Safety: All 4 categories at BLOCK_ONLY_HIGH
   - Result: ❌ BLOCKED (Finish Reason: SAFETY)

2. RETRY 1
   - Sends: Question ONLY (no context)
   - Temperature: 0.2 (more predictable)
   - Max tokens: 300
   - Result: ✅ SUCCESS → Returns advice

User gets maize farming advice!
```

### Scenario: Even more restrictive blocks

```
1. FIRST ATTEMPT → ❌ BLOCKED
2. RETRY 1 (no context) → ❌ BLOCKED
3. RETRY 2 (minimal settings) → ✅ SUCCESS

User gets advice from Retry 2
```

---

## Testing the Fix

### Enable Debug Mode:
```bash
export ADVICE_DEBUG=true
```

### Make a Test Request:
```bash
curl -X POST http://localhost:8088/advice \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "farmer_test",
    "analytics_context": {"crop_type": "maize"},
    "question": "What disease management techniques work best for maize?",
    "conversation_id": "test_123"
  }'
```

### Expected Debug Output:
```
=== ADVICE DEBUG: Prompt sent to model ===
You are a licensed agricultural extension officer...
=== END PROMPT ===

⚠️  Response blocked - Finish Reason: SAFETY
   Safety Rating: HARM_CATEGORY_DANGEROUS_CONTENT -> MEDIUM

🔄 Retry 1: Removing contexts...
✅ Retry 1 succeeded: 287 chars

Response: 287 chars of actual farming advice!
```

---

## How to Deploy

### Step 1: Pull Latest Code
```bash
cd /home/kerich/Documents/SHAMBABORA/rag-service
git pull origin master
```

### Step 2: Restart Service
```bash
docker-compose down
export ADVICE_DEBUG=true  # Optional, for troubleshooting
docker-compose up --build
```

### Step 3: Verify Fix
```bash
# Test any farming question
curl -X POST http://localhost:8088/advice \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "analytics_context": {"crop_type": "maize"}, "question": "Best practices for maize?", "conversation_id": "test"}'

# Should get actual advice, not:
# "I cannot provide advice due to safety restrictions"
```

---

## Key Changes in `generator.py`

1. **Lines 11-26**: Added `SAFETY_TRIGGER_WORDS` mapping
2. **Lines 28-36**: Added `sanitize_context_for_safety()` function
3. **Lines 70-79**: Updated prompt to use sanitized contexts
4. **Lines 80-81**: Reduced context chunk size to 600 chars
5. **Lines 154-195**: Implemented two-tier retry strategy

---

## If Still Having Issues

### Check logs with debug mode:
```bash
export ADVICE_DEBUG=true
# Look for which SAFETY category is blocking
```

### If `HARM_CATEGORY_DANGEROUS_CONTENT` still blocks:
- The question itself may have risky keywords
- Try to make user questions more specific
- Example: Instead of "How to kill weeds?" → "What herbicides work for maize?"

### If retries still fail:
- Consider using Claude or open-source alternative
- Or implement question pre-filtering to catch risky questions early

---

## Files Modified
- ✅ `app/generator.py` - Context sanitization + multi-tier retry

## Status
🟢 Context sanitization implemented - Should now handle most agriculture-related safety blocks!
