# Integration Guide for Mobile & Frontend Developers

This guide provides complete examples for integrating the RAG service into your mobile apps and web frontends.

## Table of Contents

- [React Native (Mobile)](#react-native-mobile)
- [Flutter (Mobile)](#flutter-mobile)
- [React (Web)](#react-web)
- [Vue.js (Web)](#vuejs-web)
- [Angular (Web)](#angular-web)
- [Swift (iOS)](#swift-ios)
- [Kotlin (Android)](#kotlin-android)

---

## React Native (Mobile)

### Installation

```bash
npm install axios
# or
yarn add axios
```

### Service Class

```typescript
// services/RAGService.ts
import axios from 'axios';

const BASE_URL = 'http://localhost:8088'; // Change to your production URL

export interface QueryRequest {
  question: string;
  user_id: string;
  conversation_id?: string;
  k?: number;
}

export interface QueryResponse {
  answer: string;
  contexts: Context[];
  conversation_id: string;
}

export interface Context {
  score: number;
  id: string;
  text: string;
  metadata?: any;
}

export interface Conversation {
  conversation_id: string;
  user_id: string;
  title: string;
  messages: Message[];
  created_at: string;
  updated_at: string;
}

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  contexts?: Context[];
}

class RAGService {
  private baseURL: string;

  constructor(baseURL: string = BASE_URL) {
    this.baseURL = baseURL;
  }

  async query(request: QueryRequest): Promise<QueryResponse> {
    const response = await axios.post(`${this.baseURL}/query`, request);
    return response.data;
  }

  async createConversation(userId: string, title?: string): Promise<Conversation> {
    const response = await axios.post(`${this.baseURL}/conversations`, {
      user_id: userId,
      title: title || 'New Conversation',
    });
    return response.data;
  }

  async getConversation(conversationId: string): Promise<Conversation> {
    const response = await axios.get(`${this.baseURL}/conversations/${conversationId}`);
    return response.data;
  }

  async getUserConversations(userId: string, limit: number = 50): Promise<any[]> {
    const response = await axios.get(`${this.baseURL}/users/${userId}/conversations`, {
      params: { limit },
    });
    return response.data;
  }

  async deleteConversation(conversationId: string, userId: string): Promise<void> {
    await axios.delete(`${this.baseURL}/conversations/${conversationId}`, {
      params: { user_id: userId },
    });
  }

  async uploadFiles(files: File[]): Promise<any> {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    
    const response = await axios.post(`${this.baseURL}/ingest/files`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  }
}

export default new RAGService();
```

### Chat Screen Component

```typescript
// screens/ChatScreen.tsx
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import RAGService, { Message } from '../services/RAGService';

const ChatScreen = ({ route }) => {
  const { userId } = route.params;
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);

  const sendMessage = async () => {
    if (!inputText.trim()) return;

    const userMessage: Message = {
      role: 'user',
      content: inputText,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setLoading(true);

    try {
      const response = await RAGService.query({
        question: inputText,
        user_id: userId,
        conversation_id: conversationId || undefined,
        k: 4,
      });

      setConversationId(response.conversation_id);

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.answer,
        timestamp: new Date().toISOString(),
        contexts: response.contexts,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      // Handle error (show toast, etc.)
    } finally {
      setLoading(false);
    }
  };

  const renderMessage = ({ item }: { item: Message }) => (
    <View
      style={[
        styles.messageBubble,
        item.role === 'user' ? styles.userBubble : styles.assistantBubble,
      ]}
    >
      <Text style={styles.messageText}>{item.content}</Text>
      <Text style={styles.timestamp}>
        {new Date(item.timestamp).toLocaleTimeString()}
      </Text>
    </View>
  );

  return (
    <View style={styles.container}>
      <FlatList
        data={messages}
        renderItem={renderMessage}
        keyExtractor={(_, index) => index.toString()}
        contentContainerStyle={styles.messageList}
      />
      
      <View style={styles.inputContainer}>
        <TextInput
          style={styles.input}
          value={inputText}
          onChangeText={setInputText}
          placeholder="Ask about maize farming..."
          multiline
        />
        <TouchableOpacity
          style={styles.sendButton}
          onPress={sendMessage}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.sendButtonText}>Send</Text>
          )}
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  messageList: {
    padding: 16,
  },
  messageBubble: {
    maxWidth: '80%',
    padding: 12,
    borderRadius: 16,
    marginBottom: 8,
  },
  userBubble: {
    alignSelf: 'flex-end',
    backgroundColor: '#007AFF',
  },
  assistantBubble: {
    alignSelf: 'flex-start',
    backgroundColor: '#fff',
  },
  messageText: {
    fontSize: 16,
    color: '#000',
  },
  timestamp: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 16,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
  },
  input: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginRight: 8,
    maxHeight: 100,
  },
  sendButton: {
    backgroundColor: '#007AFF',
    borderRadius: 20,
    paddingHorizontal: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendButtonText: {
    color: '#fff',
    fontWeight: 'bold',
  },
});

export default ChatScreen;
```

---

## Flutter (Mobile)

### Dependencies

```yaml
# pubspec.yaml
dependencies:
  http: ^1.1.0
  provider: ^6.0.5
```

### Service Class

```dart
// lib/services/rag_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class RAGService {
  final String baseUrl;

  RAGService({this.baseUrl = 'http://localhost:8088'});

  Future<QueryResponse> query({
    required String question,
    required String userId,
    String? conversationId,
    int k = 4,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/query'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'question': question,
        'user_id': userId,
        'conversation_id': conversationId,
        'k': k,
      }),
    );

    if (response.statusCode == 200) {
      return QueryResponse.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Failed to query: ${response.body}');
    }
  }

  Future<Conversation> createConversation({
    required String userId,
    String? title,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/conversations'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'user_id': userId,
        'title': title ?? 'New Conversation',
      }),
    );

    if (response.statusCode == 200) {
      return Conversation.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Failed to create conversation');
    }
  }

  Future<List<ConversationSummary>> getUserConversations({
    required String userId,
    int limit = 50,
  }) async {
    final response = await http.get(
      Uri.parse('$baseUrl/users/$userId/conversations?limit=$limit'),
    );

    if (response.statusCode == 200) {
      final List<dynamic> data = jsonDecode(response.body);
      return data.map((json) => ConversationSummary.fromJson(json)).toList();
    } else {
      throw Exception('Failed to load conversations');
    }
  }
}

class QueryResponse {
  final String answer;
  final List<Context> contexts;
  final String conversationId;

  QueryResponse({
    required this.answer,
    required this.contexts,
    required this.conversationId,
  });

  factory QueryResponse.fromJson(Map<String, dynamic> json) {
    return QueryResponse(
      answer: json['answer'],
      contexts: (json['contexts'] as List)
          .map((c) => Context.fromJson(c))
          .toList(),
      conversationId: json['conversation_id'],
    );
  }
}

class Context {
  final double score;
  final String id;
  final String text;

  Context({required this.score, required this.id, required this.text});

  factory Context.fromJson(Map<String, dynamic> json) {
    return Context(
      score: json['score'].toDouble(),
      id: json['id'],
      text: json['text'],
    );
  }
}

class Conversation {
  final String conversationId;
  final String userId;
  final String title;
  final List<Message> messages;

  Conversation({
    required this.conversationId,
    required this.userId,
    required this.title,
    required this.messages,
  });

  factory Conversation.fromJson(Map<String, dynamic> json) {
    return Conversation(
      conversationId: json['conversation_id'],
      userId: json['user_id'],
      title: json['title'],
      messages: (json['messages'] as List)
          .map((m) => Message.fromJson(m))
          .toList(),
    );
  }
}

class Message {
  final String role;
  final String content;
  final DateTime timestamp;

  Message({
    required this.role,
    required this.content,
    required this.timestamp,
  });

  factory Message.fromJson(Map<String, dynamic> json) {
    return Message(
      role: json['role'],
      content: json['content'],
      timestamp: DateTime.parse(json['timestamp']),
    );
  }
}

class ConversationSummary {
  final String conversationId;
  final String title;
  final int messageCount;
  final String? lastMessage;

  ConversationSummary({
    required this.conversationId,
    required this.title,
    required this.messageCount,
    this.lastMessage,
  });

  factory ConversationSummary.fromJson(Map<String, dynamic> json) {
    return ConversationSummary(
      conversationId: json['conversation_id'],
      title: json['title'],
      messageCount: json['message_count'],
      lastMessage: json['last_message'],
    );
  }
}
```

### Chat Screen Widget

```dart
// lib/screens/chat_screen.dart
import 'package:flutter/material.dart';
import '../services/rag_service.dart';

class ChatScreen extends StatefulWidget {
  final String userId;

  const ChatScreen({Key? key, required this.userId}) : super(key: key);

  @override
  _ChatScreenState createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final RAGService _ragService = RAGService();
  final TextEditingController _controller = TextEditingController();
  final List<Message> _messages = [];
  String? _conversationId;
  bool _loading = false;

  Future<void> _sendMessage() async {
    if (_controller.text.trim().isEmpty) return;

    final userMessage = Message(
      role: 'user',
      content: _controller.text,
      timestamp: DateTime.now(),
    );

    setState(() {
      _messages.add(userMessage);
      _loading = true;
    });

    final question = _controller.text;
    _controller.clear();

    try {
      final response = await _ragService.query(
        question: question,
        userId: widget.userId,
        conversationId: _conversationId,
      );

      setState(() {
        _conversationId = response.conversationId;
        _messages.add(Message(
          role: 'assistant',
          content: response.answer,
          timestamp: DateTime.now(),
        ));
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Maize Farming Assistant')),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              padding: EdgeInsets.all(16),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final message = _messages[index];
                final isUser = message.role == 'user';
                
                return Align(
                  alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin: EdgeInsets.only(bottom: 8),
                    padding: EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: isUser ? Colors.blue : Colors.grey[300],
                      borderRadius: BorderRadius.circular(16),
                    ),
                    constraints: BoxConstraints(
                      maxWidth: MediaQuery.of(context).size.width * 0.8,
                    ),
                    child: Text(
                      message.content,
                      style: TextStyle(
                        color: isUser ? Colors.white : Colors.black,
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
          Container(
            padding: EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Colors.black12,
                  blurRadius: 4,
                  offset: Offset(0, -2),
                ),
              ],
            ),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    decoration: InputDecoration(
                      hintText: 'Ask about maize farming...',
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(24),
                      ),
                    ),
                    maxLines: null,
                  ),
                ),
                SizedBox(width: 8),
                FloatingActionButton(
                  onPressed: _loading ? null : _sendMessage,
                  child: _loading
                      ? CircularProgressIndicator(color: Colors.white)
                      : Icon(Icons.send),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
```

---

## React (Web)

### Custom Hook

```typescript
// hooks/useRAGService.ts
import { useState, useCallback } from 'react';
import axios from 'axios';

const BASE_URL = 'http://localhost:8088';

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  contexts?: any[];
}

export const useRAGService = (userId: string) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);

  const sendMessage = useCallback(async (question: string) => {
    const userMessage: Message = {
      role: 'user',
      content: question,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setLoading(true);

    try {
      const response = await axios.post(`${BASE_URL}/query`, {
        question,
        user_id: userId,
        conversation_id: conversationId,
        k: 4,
      });

      setConversationId(response.data.conversation_id);

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.answer,
        timestamp: new Date().toISOString(),
        contexts: response.data.contexts,
      };

      setMessages(prev => [...prev, assistantMessage]);
      return response.data;
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [userId, conversationId]);

  const loadConversation = useCallback(async (convId: string) => {
    try {
      const response = await axios.get(`${BASE_URL}/conversations/${convId}`);
      setConversationId(convId);
      setMessages(response.data.messages);
    } catch (error) {
      console.error('Error loading conversation:', error);
      throw error;
    }
  }, []);

  return {
    messages,
    loading,
    conversationId,
    sendMessage,
    loadConversation,
  };
};
```

### Chat Component

```typescript
// components/ChatInterface.tsx
import React, { useState, useRef, useEffect } from 'react';
import { useRAGService } from '../hooks/useRAGService';
import './ChatInterface.css';

interface ChatInterfaceProps {
  userId: string;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ userId }) => {
  const [input, setInput] = useState('');
  const { messages, loading, sendMessage } = useRAGService(userId);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    try {
      await sendMessage(input);
      setInput('');
    } catch (error) {
      alert('Failed to send message');
    }
  };

  return (
    <div className="chat-container">
      <div className="messages-container">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`message ${message.role === 'user' ? 'user' : 'assistant'}`}
          >
            <div className="message-content">{message.content}</div>
            <div className="message-timestamp">
              {new Date(message.timestamp).toLocaleTimeString()}
            </div>
          </div>
        ))}
        {loading && (
          <div className="message assistant">
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form className="input-container" onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about maize farming..."
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
};
```

---

## Quick Reference

### Base URL
```
http://localhost:8088
```

### Essential Endpoints

1. **Query**: `POST /query`
2. **Create Conversation**: `POST /conversations`
3. **Get Conversations**: `GET /users/{user_id}/conversations`
4. **Get Conversation**: `GET /conversations/{id}`

### Common Patterns

**New Conversation:**
```json
POST /query
{
  "question": "How to plant maize?",
  "user_id": "user123"
}
```

**Continue Conversation:**
```json
POST /query
{
  "question": "What about fertilizer?",
  "user_id": "user123",
  "conversation_id": "existing-id"
}
```

---

For complete API documentation, see [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
