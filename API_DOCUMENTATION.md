# Professional Maize RAG Service - API Documentation

## Overview

A production-ready Retrieval-Augmented Generation (RAG) service for agricultural advisory, specifically focused on maize farming. This service provides AI-powered answers with conversation history tracking, making it perfect for mobile apps and web frontends.

**Version:** 2.0.0  
**Base URL:** `http://localhost:8088` (or your deployed URL)

## Features

- ✅ **Intelligent Q&A** - AI-powered answers using RAG architecture
- ✅ **Conversation History** - Track and manage user conversations
- ✅ **Document Ingestion** - Support for PDF and text files
- ✅ **Context Retrieval** - Semantic search with FAISS
- ✅ **User Sessions** - Multi-user support with user IDs
- ✅ **RESTful API** - Clean, well-documented endpoints
- ✅ **CORS Enabled** - Ready for web and mobile integration

## Tech Stack

- **Framework:** FastAPI
- **Embeddings:** Ollama (nomic-embed-text)
- **Generation:** Google Gemini (gemini-1.5-flash)
- **Vector Store:** FAISS
- **Database:** JSON-based file storage

---

## Quick Start

### Prerequisites

1. **Python 3.8+**
2. **Ollama** installed and running (for embeddings)
3. **Google API Key** (for Gemini)

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd rag-service

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### Environment Variables

Create a `.env` file:

```env
GOOGLE_API_KEY=your_google_api_key_here
EMBEDDING_MODEL=nomic-embed-text
GENERATION_MODEL=gemini-1.5-flash
INDEX_DIR=data
CONVERSATION_DIR=data/conversations
PORT=8088
```

### Running the Service

```bash
# Start Ollama (in a separate terminal)
ollama serve

# Pull the embedding model
ollama pull nomic-embed-text

# Start the RAG service
uvicorn app.main:app --host 0.0.0.0 --port 8088 --reload
```

The API will be available at:
- **API:** http://localhost:8088
- **Interactive Docs:** http://localhost:8088/docs
- **ReDoc:** http://localhost:8088/redoc

---

## API Endpoints

### System

#### Health Check
```http
GET /health
```

**Response:**
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

---

### Document Management

#### Ingest Documents
```http
POST /ingest
Content-Type: application/json
```

**Request Body:**
```json
{
  "documents": [
    {
      "id": "doc1",
      "text": "Maize requires well-drained soil with pH 5.5-7.0...",
      "metadata": {
        "source": "farming_guide",
        "category": "soil"
      }
    }
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Documents ingested successfully",
  "count": 1
}
```

#### Upload Files
```http
POST /ingest/files
Content-Type: multipart/form-data
```

**Request:**
- Form field: `files` (multiple files supported)
- Supported formats: PDF, TXT

**Response:**
```json
{
  "status": "success",
  "message": "Files ingested successfully",
  "count": 2,
  "files": ["maize_guide.pdf", "farming_tips.txt"]
}
```

---

### Query

#### Ask a Question
```http
POST /query
Content-Type: application/json
```

**Request Body:**
```json
{
  "question": "What is the best soil pH for maize?",
  "k": 4,
  "conversation_id": "optional-conversation-id",
  "user_id": "user123"
}
```

**Parameters:**
- `question` (required): The question to ask
- `k` (optional, default: 4): Number of context documents to retrieve (1-10)
- `conversation_id` (optional): Existing conversation ID, or omit to create new
- `user_id` (required): User identifier

**Response:**
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

---

### Conversations

#### Create Conversation
```http
POST /conversations
Content-Type: application/json
```

**Request Body:**
```json
{
  "user_id": "user123",
  "title": "Maize Farming Questions",
  "metadata": {
    "platform": "mobile",
    "app_version": "1.0.0"
  }
}
```

**Response:**
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user123",
  "title": "Maize Farming Questions",
  "messages": [],
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00",
  "metadata": {
    "platform": "mobile",
    "app_version": "1.0.0"
  }
}
```

#### Get Conversation
```http
GET /conversations/{conversation_id}
```

**Response:**
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user123",
  "title": "Maize Farming Questions",
  "messages": [
    {
      "role": "user",
      "content": "What is the best soil pH for maize?",
      "timestamp": "2024-01-01T12:00:00",
      "contexts": null
    },
    {
      "role": "assistant",
      "content": "The optimal soil pH for maize...",
      "timestamp": "2024-01-01T12:00:05",
      "contexts": [...]
    }
  ],
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:05",
  "metadata": {}
}
```

#### List User Conversations
```http
GET /users/{user_id}/conversations?limit=50&offset=0
```

**Query Parameters:**
- `limit` (optional, default: 50): Maximum conversations to return (1-100)
- `offset` (optional, default: 0): Number of conversations to skip

**Response:**
```json
[
  {
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "user123",
    "title": "Maize Farming Questions",
    "message_count": 4,
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:30:00",
    "last_message": "The optimal soil pH for maize..."
  }
]
```

#### Update Conversation
```http
PATCH /conversations/{conversation_id}
Content-Type: application/json
```

**Request Body:**
```json
{
  "title": "Updated Title",
  "metadata": {
    "archived": false
  }
}
```

**Response:**
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user123",
  "title": "Updated Title",
  "messages": [...],
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T13:00:00",
  "metadata": {
    "archived": false
  }
}
```

#### Delete Conversation
```http
DELETE /conversations/{conversation_id}?user_id=user123
```

**Query Parameters:**
- `user_id` (required): User ID for authorization

**Response:**
```json
{
  "status": "success",
  "message": "Conversation deleted successfully"
}
```

---

## Integration Examples

### Mobile App (React Native / Flutter)

#### Initialize a Conversation
```javascript
// Create a new conversation
const response = await fetch('http://localhost:8088/conversations', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    user_id: 'user123',
    title: 'My Farming Questions',
  }),
});

const conversation = await response.json();
const conversationId = conversation.conversation_id;
```

#### Ask a Question
```javascript
// Ask a question in the conversation
const response = await fetch('http://localhost:8088/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    question: 'What is the best time to plant maize?',
    user_id: 'user123',
    conversation_id: conversationId,
    k: 4,
  }),
});

const result = await response.json();
console.log('Answer:', result.answer);
console.log('Contexts:', result.contexts);
```

#### Load Conversation History
```javascript
// Get all conversations for a user
const response = await fetch('http://localhost:8088/users/user123/conversations?limit=20');
const conversations = await response.json();

// Get specific conversation with messages
const detailResponse = await fetch(`http://localhost:8088/conversations/${conversationId}`);
const conversationDetail = await detailResponse.json();
console.log('Messages:', conversationDetail.messages);
```

### Web Frontend (React / Vue / Angular)

#### TypeScript Types
```typescript
interface QueryRequest {
  question: string;
  user_id: string;
  conversation_id?: string;
  k?: number;
}

interface QueryResponse {
  answer: string;
  contexts: Context[];
  conversation_id: string;
}

interface Context {
  score: number;
  id: string;
  text: string;
  metadata?: Record<string, any>;
}

interface Conversation {
  conversation_id: string;
  user_id: string;
  title: string;
  messages: Message[];
  created_at: string;
  updated_at: string;
  metadata?: Record<string, any>;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  contexts?: Context[];
}
```

#### React Hook Example
```typescript
import { useState, useEffect } from 'react';

const useRAGService = (userId: string) => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(false);

  const askQuestion = async (question: string, conversationId?: string) => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8088/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question,
          user_id: userId,
          conversation_id: conversationId,
          k: 4,
        }),
      });
      const result = await response.json();
      return result;
    } finally {
      setLoading(false);
    }
  };

  const loadConversations = async () => {
    const response = await fetch(`http://localhost:8088/users/${userId}/conversations`);
    const data = await response.json();
    setConversations(data);
  };

  useEffect(() => {
    loadConversations();
  }, [userId]);

  return { conversations, askQuestion, loadConversations, loading };
};
```

### Python Client Example
```python
import requests

class RAGClient:
    def __init__(self, base_url: str, user_id: str):
        self.base_url = base_url
        self.user_id = user_id
    
    def create_conversation(self, title: str = None):
        response = requests.post(
            f"{self.base_url}/conversations",
            json={"user_id": self.user_id, "title": title}
        )
        return response.json()
    
    def ask_question(self, question: str, conversation_id: str = None, k: int = 4):
        response = requests.post(
            f"{self.base_url}/query",
            json={
                "question": question,
                "user_id": self.user_id,
                "conversation_id": conversation_id,
                "k": k
            }
        )
        return response.json()
    
    def get_conversations(self, limit: int = 50):
        response = requests.get(
            f"{self.base_url}/users/{self.user_id}/conversations",
            params={"limit": limit}
        )
        return response.json()

# Usage
client = RAGClient("http://localhost:8088", "user123")
conversation = client.create_conversation("Maize Farming")
result = client.ask_question(
    "What is the best soil pH for maize?",
    conversation_id=conversation["conversation_id"]
)
print(result["answer"])
```

---

## Error Handling

All endpoints return standard HTTP status codes:

- **200 OK** - Successful request
- **400 Bad Request** - Invalid request parameters
- **404 Not Found** - Resource not found
- **422 Unprocessable Entity** - Validation error
- **500 Internal Server Error** - Server error

**Error Response Format:**
```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## Best Practices

### For Mobile Apps

1. **User IDs**: Use device ID or authenticated user ID
2. **Conversation Management**: Create a new conversation for each topic
3. **Caching**: Cache conversation lists locally
4. **Error Handling**: Implement retry logic for network failures
5. **Loading States**: Show loading indicators during API calls

### For Web Frontends

1. **State Management**: Use Redux/Vuex for conversation state
2. **Optimistic Updates**: Update UI before API confirmation
3. **Pagination**: Implement infinite scroll for conversation lists
4. **Real-time Updates**: Consider WebSocket for live updates (future feature)
5. **Accessibility**: Ensure chat interface is screen-reader friendly

### General

1. **Rate Limiting**: Implement client-side rate limiting
2. **Context Size**: Use `k=3-5` for optimal performance
3. **User Sessions**: Maintain user_id consistently across sessions
4. **Metadata**: Use metadata fields for app-specific tracking
5. **Conversation Titles**: Auto-generated from first message, but allow updates

---

## Performance Considerations

- **Embedding Generation**: ~100-500ms per query (depends on Ollama)
- **Answer Generation**: ~1-3s per query (depends on Gemini)
- **Context Retrieval**: <50ms for most queries
- **Conversation Storage**: JSON-based, suitable for <10k conversations per user

For production deployments with high traffic:
- Consider PostgreSQL for conversation storage
- Implement Redis caching for frequently accessed conversations
- Use connection pooling for database connections
- Deploy behind a load balancer

---

## Security Considerations

⚠️ **Important**: This is a development version. For production:

1. **Authentication**: Implement JWT or OAuth2
2. **Authorization**: Verify user_id ownership
3. **Rate Limiting**: Add rate limiting middleware
4. **Input Validation**: Sanitize all user inputs
5. **HTTPS**: Always use HTTPS in production
6. **API Keys**: Store API keys securely (use secrets manager)
7. **CORS**: Restrict origins to your domains

---

## Deployment

### Docker Deployment

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8088

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8088"]
```

### Environment Variables for Production

```env
GOOGLE_API_KEY=your_production_key
EMBEDDING_MODEL=nomic-embed-text
GENERATION_MODEL=gemini-1.5-flash
INDEX_DIR=/data/index
CONVERSATION_DIR=/data/conversations
PORT=8088
```

---

## Support & Contributing

For issues, questions, or contributions:
- Create an issue on GitHub
- Submit a pull request
- Contact: [your-email@example.com]

---

## License

[Your License Here]

---

## Changelog

### Version 2.0.0 (Current)
- ✅ Added conversation history tracking
- ✅ Added user session management
- ✅ Enhanced API documentation
- ✅ Added conversation CRUD operations
- ✅ Improved error handling
- ✅ Added health check endpoint

### Version 1.2.0
- Initial RAG implementation
- Document ingestion
- Basic query endpoint

---

**Built with ❤️ for farmers**
