# Testing Guide

Complete guide for testing your RAG service API.

## Quick Test

### 1. Health Check
```bash
curl http://localhost:8088/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "timestamp": "2024-01-01T12:00:00",
  "services": {
    "retriever": "operational",
    "generator": "operational",
    "database": "operational"
  }
}
```

## Complete Test Flow

### Step 1: Ingest Sample Data

```bash
curl -X POST "http://localhost:8088/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {
        "id": "doc1",
        "text": "Maize requires well-drained soil with pH between 5.5 and 7.0. The crop grows best in warm conditions with temperatures between 20-30°C.",
        "metadata": {
          "source": "farming_guide",
          "category": "soil"
        }
      },
      {
        "id": "doc2",
        "text": "Plant maize seeds 2-3 cm deep with spacing of 75cm between rows and 25cm between plants. Optimal planting time is at the beginning of the rainy season.",
        "metadata": {
          "source": "planting_guide",
          "category": "planting"
        }
      },
      {
        "id": "doc3",
        "text": "Apply nitrogen fertilizer in split doses: 1/3 at planting, 1/3 at 4 weeks, and 1/3 at 8 weeks after planting. Use NPK 23:23:0 or similar compound fertilizer.",
        "metadata": {
          "source": "fertilizer_guide",
          "category": "fertilization"
        }
      }
    ]
  }'
```

### Step 2: Create a Conversation

```bash
curl -X POST "http://localhost:8088/conversations" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_123",
    "title": "My Farming Questions"
  }'
```

**Save the `conversation_id` from the response!**

### Step 3: Ask First Question

```bash
curl -X POST "http://localhost:8088/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the best soil pH for maize?",
    "user_id": "test_user_123",
    "k": 4
  }'
```

**Note:** This will auto-create a conversation if you don't provide `conversation_id`.

### Step 4: Continue the Conversation

```bash
# Replace YOUR_CONVERSATION_ID with the actual ID from step 3
curl -X POST "http://localhost:8088/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How should I apply fertilizer?",
    "user_id": "test_user_123",
    "conversation_id": "YOUR_CONVERSATION_ID",
    "k": 4
  }'
```

### Step 5: View Conversation History

```bash
curl "http://localhost:8088/conversations/YOUR_CONVERSATION_ID"
```

### Step 6: List All User Conversations

```bash
curl "http://localhost:8088/users/test_user_123/conversations"
```

### Step 7: Update Conversation

```bash
curl -X PATCH "http://localhost:8088/conversations/YOUR_CONVERSATION_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Maize Farming Guide - Updated"
  }'
```

### Step 8: Delete Conversation

```bash
curl -X DELETE "http://localhost:8088/conversations/YOUR_CONVERSATION_ID?user_id=test_user_123"
```

## Using Postman

### Import Collection

1. Open Postman
2. Click **Import**
3. Select `postman_collection.json`
4. Collection will be imported with all endpoints

### Set Variables

In the collection variables:
- `base_url`: `http://localhost:8088`
- `user_id`: `test_user_123`
- `conversation_id`: (auto-populated by tests)

### Run Tests

1. **Health Check** - Verify service is running
2. **Ingest Documents** - Add sample data
3. **Query (New Conversation)** - Creates conversation automatically
4. **Query (Continue)** - Uses saved conversation_id
5. **List Conversations** - View all user conversations

## Using Swagger UI

1. Open browser: http://localhost:8088/docs
2. Click on any endpoint
3. Click **Try it out**
4. Fill in parameters
5. Click **Execute**

### Recommended Test Order in Swagger

1. `GET /health` - Check service
2. `POST /ingest` - Add documents
3. `POST /conversations` - Create conversation
4. `POST /query` - Ask questions
5. `GET /users/{user_id}/conversations` - List conversations
6. `GET /conversations/{conversation_id}` - View details

## Test Scenarios

### Scenario 1: New User First Query

```bash
# User asks first question (no conversation_id)
curl -X POST "http://localhost:8088/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How do I plant maize?",
    "user_id": "new_user_456"
  }'

# Response includes new conversation_id
# Use it for follow-up questions
```

### Scenario 2: Multi-Turn Conversation

```bash
# Question 1
curl -X POST "http://localhost:8088/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What soil pH does maize need?",
    "user_id": "user_789"
  }'

# Save conversation_id from response

# Question 2 (same conversation)
curl -X POST "http://localhost:8088/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What about temperature requirements?",
    "user_id": "user_789",
    "conversation_id": "SAVED_CONVERSATION_ID"
  }'

# Question 3 (same conversation)
curl -X POST "http://localhost:8088/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "When should I plant?",
    "user_id": "user_789",
    "conversation_id": "SAVED_CONVERSATION_ID"
  }'
```

### Scenario 3: Multiple Conversations

```bash
# Create conversation 1
curl -X POST "http://localhost:8088/conversations" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "title": "Soil Questions"
  }'

# Create conversation 2
curl -X POST "http://localhost:8088/conversations" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "title": "Planting Questions"
  }'

# List all conversations
curl "http://localhost:8088/users/user_123/conversations"
```

### Scenario 4: File Upload

```bash
# Upload a PDF file
curl -X POST "http://localhost:8088/ingest/files" \
  -F "files=@maize_guide.pdf"

# Upload multiple files
curl -X POST "http://localhost:8088/ingest/files" \
  -F "files=@guide1.pdf" \
  -F "files=@guide2.txt"
```

## Python Test Script

```python
import requests
import json

BASE_URL = "http://localhost:8088"
USER_ID = "test_user_python"

def test_complete_flow():
    # 1. Health check
    print("1. Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {response.json()['status']}")
    
    # 2. Ingest documents
    print("\n2. Ingesting documents...")
    response = requests.post(
        f"{BASE_URL}/ingest",
        json={
            "documents": [
                {
                    "id": "test_doc",
                    "text": "Maize needs pH 5.5-7.0 soil.",
                    "metadata": {"source": "test"}
                }
            ]
        }
    )
    print(f"   Ingested: {response.json()['count']} documents")
    
    # 3. Create conversation
    print("\n3. Creating conversation...")
    response = requests.post(
        f"{BASE_URL}/conversations",
        json={
            "user_id": USER_ID,
            "title": "Test Conversation"
        }
    )
    conversation_id = response.json()["conversation_id"]
    print(f"   Conversation ID: {conversation_id}")
    
    # 4. Ask question
    print("\n4. Asking question...")
    response = requests.post(
        f"{BASE_URL}/query",
        json={
            "question": "What soil pH does maize need?",
            "user_id": USER_ID,
            "conversation_id": conversation_id
        }
    )
    answer = response.json()["answer"]
    print(f"   Answer: {answer[:100]}...")
    
    # 5. List conversations
    print("\n5. Listing conversations...")
    response = requests.get(
        f"{BASE_URL}/users/{USER_ID}/conversations"
    )
    conversations = response.json()
    print(f"   Found {len(conversations)} conversation(s)")
    
    # 6. Get conversation details
    print("\n6. Getting conversation details...")
    response = requests.get(
        f"{BASE_URL}/conversations/{conversation_id}"
    )
    messages = response.json()["messages"]
    print(f"   Messages: {len(messages)}")
    
    # 7. Delete conversation
    print("\n7. Deleting conversation...")
    response = requests.delete(
        f"{BASE_URL}/conversations/{conversation_id}",
        params={"user_id": USER_ID}
    )
    print(f"   Status: {response.json()['status']}")
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    test_complete_flow()
```

## JavaScript Test Script

```javascript
const BASE_URL = 'http://localhost:8088';
const USER_ID = 'test_user_js';

async function testCompleteFlow() {
  try {
    // 1. Health check
    console.log('1. Testing health check...');
    let response = await fetch(`${BASE_URL}/health`);
    let data = await response.json();
    console.log(`   Status: ${data.status}`);

    // 2. Ingest documents
    console.log('\n2. Ingesting documents...');
    response = await fetch(`${BASE_URL}/ingest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        documents: [
          {
            id: 'test_doc',
            text: 'Maize needs pH 5.5-7.0 soil.',
            metadata: { source: 'test' }
          }
        ]
      })
    });
    data = await response.json();
    console.log(`   Ingested: ${data.count} documents`);

    // 3. Create conversation
    console.log('\n3. Creating conversation...');
    response = await fetch(`${BASE_URL}/conversations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: USER_ID,
        title: 'Test Conversation'
      })
    });
    data = await response.json();
    const conversationId = data.conversation_id;
    console.log(`   Conversation ID: ${conversationId}`);

    // 4. Ask question
    console.log('\n4. Asking question...');
    response = await fetch(`${BASE_URL}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question: 'What soil pH does maize need?',
        user_id: USER_ID,
        conversation_id: conversationId
      })
    });
    data = await response.json();
    console.log(`   Answer: ${data.answer.substring(0, 100)}...`);

    // 5. List conversations
    console.log('\n5. Listing conversations...');
    response = await fetch(`${BASE_URL}/users/${USER_ID}/conversations`);
    data = await response.json();
    console.log(`   Found ${data.length} conversation(s)`);

    console.log('\n✅ All tests passed!');
  } catch (error) {
    console.error('❌ Test failed:', error);
  }
}

testCompleteFlow();
```

## Expected Results

### Successful Query Response
```json
{
  "answer": "The optimal soil pH for maize cultivation is between 5.5 and 7.0...",
  "contexts": [
    {
      "score": 0.89,
      "id": "doc1",
      "text": "Maize requires well-drained soil...",
      "metadata": {
        "source": "farming_guide"
      }
    }
  ],
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Conversation with History
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "test_user_123",
  "title": "Maize Farming Questions",
  "messages": [
    {
      "role": "user",
      "content": "What is the best soil pH for maize?",
      "timestamp": "2024-01-01T12:00:00"
    },
    {
      "role": "assistant",
      "content": "The optimal soil pH...",
      "timestamp": "2024-01-01T12:00:05",
      "contexts": [...]
    }
  ],
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:05"
}
```

## Troubleshooting

### Service Not Responding
```bash
# Check if service is running
curl http://localhost:8088/health

# Check logs
# (if running with uvicorn --reload)
```

### "Conversation not found"
- Verify conversation_id is correct
- Check if conversation was deleted
- Ensure user_id matches

### Empty Contexts
- Ingest documents first
- Check if Ollama is running
- Verify embedding model is pulled

### Slow Responses
- Normal: 1-3 seconds per query
- Check Ollama performance
- Check Google API rate limits

## Performance Testing

### Load Test with Apache Bench
```bash
# Test health endpoint
ab -n 100 -c 10 http://localhost:8088/health

# Test query endpoint (requires POST data file)
ab -n 10 -c 2 -p query.json -T application/json http://localhost:8088/query
```

### query.json
```json
{
  "question": "What is the best soil pH for maize?",
  "user_id": "load_test_user"
}
```

---

## Next Steps

After testing:
1. Review [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for complete API reference
2. Check [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md) for mobile/web examples
3. Start integrating into your application!

**Happy Testing! 🧪**
