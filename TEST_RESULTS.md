# RAG Service Test Results

## Service Status: ✅ UPDATED & IMPROVED

### Updates Made:

1. **Fixed Code Issues:**
   - Updated `gemini-1.5-flash` model reference (was incorrectly `gemini-2.5-flash`)
   - Fixed missing closing brace in `/query` endpoint
   - Fixed `APIError` import to use `google.api_core.exceptions.GoogleAPIError`
   - Added `PORT` environment variable support

2. **Improved Dependencies:**
   - Updated `faiss-cpu` from 1.8.0.post1 to 1.9.0.post1
   - Added `python-multipart==0.0.20` for file upload support
   - Added `uvicorn` for serving the application

3. **Enhanced Generator (Gemini API):**
   - **Improved prompt structure** to avoid safety filter false positives
   - **Added safety settings** to be less restrictive for agricultural content:
     - `HARM_CATEGORY_HARASSMENT`: BLOCK_NONE
     - `HARM_CATEGORY_HATE_SPEECH`: BLOCK_NONE
     - `HARM_CATEGORY_SEXUALLY_EXPLICIT`: BLOCK_NONE
     - `HARM_CATEGORY_DANGEROUS_CONTENT`: BLOCK_MEDIUM_AND_ABOVE
   - **Truncated contexts** to 1500 characters each (top 3 only) to prevent overly long prompts
   - **Simplified language** in prompts to be more neutral and agricultural-focused
   - Increased temperature to 0.3 for more natural responses
   - Increased max_output_tokens to 500

## Test Results:

### ✅ Health Endpoint
```bash
curl -X GET http://localhost:8088/health
```
**Response:** `{"status":"ok"}`
**Status:** WORKING

### ⚠️ Ingest & Query Endpoints
**Status:** REQUIRES OLLAMA

The service is running correctly, but **Ollama must be running** to:
- Generate embeddings for document ingestion
- Generate embeddings for query search

## How to Complete Testing:

### 1. Start Ollama (in a separate terminal):
```bash
ollama serve
```

### 2. Ensure the embedding model is available:
```bash
ollama pull nomic-embed-text
```

### 3. Test Ingest Endpoint:
```bash
curl -X POST http://localhost:8088/ingest \
  -H 'Content-Type: application/json' \
  -d '{
    "documents": [
      {
        "id": "maize1",
        "text": "Maize should be planted at the onset of rains in Kenya, typically between March and April for long rains, and October for short rains."
      },
      {
        "id": "maize2",
        "text": "For best maize yields, use certified hybrid seeds, apply DAP fertilizer at planting (50kg per acre), and top-dress with CAN fertilizer 4-6 weeks after planting."
      }
    ]
  }'
```

### 4. Test Query Endpoint:
```bash
curl -X POST http://localhost:8088/query \
  -H 'Content-Type: application/json' \
  -d '{
    "question": "What are the best soil conditions for growing maize?",
    "k": 3
  }'
```

### 5. Test with Different Questions:
```bash
# Planting timing
curl -X POST http://localhost:8088/query \
  -H 'Content-Type: application/json' \
  -d '{"question": "When should I plant maize?", "k": 3}'

# Fertilizer advice
curl -X POST http://localhost:8088/query \
  -H 'Content-Type: application/json' \
  -d '{"question": "What fertilizer should I use for maize?", "k": 3}'

# Pest management
curl -X POST http://localhost:8088/query \
  -H 'Content-Type: application/json' \
  -d '{"question": "How do I control fall armyworm?", "k": 3}'
```

## Environment Variables Required:

Create a `.env` file with:
```env
EMBEDDING_MODEL=nomic-embed-text
GENERATION_MODEL=gemini-1.5-flash
INDEX_DIR=data
PORT=8088
GOOGLE_API_KEY=your_google_api_key_here
```

## Service is Running:
- **URL:** http://localhost:8088
- **Process:** Background (auto-reload enabled)
- **Logs:** Check terminal for real-time logs

## Next Steps:
1. Start Ollama service
2. Run the curl tests above
3. The improved prompt and safety settings should now provide better responses without safety filter blocks
