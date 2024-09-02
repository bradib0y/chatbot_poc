# Web Architecture for LLM Chat Service

This document outlines the web architecture for our LLM-based chat service, detailing the structure and interaction of various components including the backend API, frontend web server, database, and LLM service integration.

## Architecture Overview

Our web architecture consists of the following main components:

0. Deployment
1. Frontend Web Application
2. Backend API Server
3. Database
4. LLM Service
5. Caching Layer
6. Load Balancer
7. (Future) Abstraction Proxy for Multiple Models
8. Chat History Retrieval and Context Management

## 0. Deployment

Our service is deployed on Azure Kubernetes Service (AKS) for scalability and ease of management.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chat-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: chat-backend
  template:
    metadata:
      labels:
        app: chat-backend
    spec:
      containers:
      - name: chat-backend
        image: your-acr.azurecr.io/chat-backend:v1
        ports:
        - containerPort: 8000
```

## 1. Frontend Web Application

The frontend is a single-page application (SPA) built with React.js, providing a responsive and interactive user interface for the chat service.

### Key Features:
- Real-time chat interface
- User authentication and profile management
- Character selection and interaction

### Implementation:

```javascript
// Example React component for chat interface
import React, { useState, useEffect } from 'react';
import axios from 'axios';

function ChatInterface({ userId, characterId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');

  const sendMessage = async () => {
    const response = await axios.post('/api/chat', { userId, characterId, message: input });
    setMessages([...messages, { user: 'You', text: input }, { user: 'AI', text: response.data.message }]);
    setInput('');
  };

  return (
    <div>
      {messages.map((msg, index) => (
        <div key={index}>{msg.user}: {msg.text}</div>
      ))}
      <input value={input} onChange={(e) => setInput(e.target.value)} />
      <button onClick={sendMessage}>Send</button>
    </div>
  );
}

export default ChatInterface;
```

## 2. Backend API Server

The backend is built with FastAPI, providing a high-performance, easy-to-use API server that interfaces between the frontend and the LLM service.

### Key Features:
- RESTful API endpoints for chat functionality
- User authentication and session management
- Integration with LLM service

### Implementation:

```python
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import crud, models, schemas
from .database import SessionLocal, engine

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/chat")
def chat(chat_request: schemas.ChatRequest, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id=chat_request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Process message with LLM service
    response = llm_service.generate_response(chat_request.message, chat_request.character_id)
    
    # Save chat message to database
    crud.create_chat_message(db, user_id=chat_request.user_id, message=chat_request.message, response=response)
    
    return {"message": response}
```

## 3. Database

We use PostgreSQL as our primary database for storing user data, chat logs, and application state.

### Key Tables:
- Users
- Characters
- ChatSessions
- ChatMessages

### Schema Example:

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    character_id INTEGER REFERENCES characters(id),
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## 4. Integration with the LLM Service

The LLM service is our custom-hosted solution for generating AI responses. It's isolated from direct internet access and is only accessible through the backend API.

### Integration:

```python
import requests

class LLMService:
    def __init__(self, base_url):
        self.base_url = base_url

    def generate_response(self, message, character_id):
        response = requests.post(f"{self.base_url}/generate", json={
            "message": message,
            "character_id": character_id
        })
        return response.json()["response"]

llm_service = LLMService("http://internal-llm-service")
```

## 5. Caching Layer

We use Redis for caching frequently accessed data and managing user sessions.

### Implementation:

```python
import redis
from fastapi import FastAPI, Depends
from fastapi_redis_cache import FastApiRedisCache, cache

app = FastAPI()
redis_cache = FastApiRedisCache()

# Add caching to the app at startup
@app.on_event("startup")
def startup():
    redis_cache.init(
        host_url="redis://localhost:6379",
        prefix="myapi-cache",
        response_header="X-MyAPI-Cache",
        ignore_arg_types=[Request, Session]
    )

# Example usage
@app.get("/api/character/{character_id}", response_model=CharacterResponse)
@cache(expire=3600) # The decorator used to mark the endpoint that caching is enabled
def get_character(character_id: int):
    # Fetch character data
    return character_data
```

## 6. Load Balancing

Load balancing is provided by the Kubernetes infrastructure, to ensure high availablity and scalability, even at times of spiking demand, and even in case of a failing backend.

## 7. (Future) Abstraction Proxy for Multiple Models

In the future, we may need to implement an abstraction proxy to support multiple LLM models. This will allow for easy switching between different providers or models.

LiteLLM is a possible tool that can be used as an abstraction proxy, or we can implement our own in the web layer.

## Chat History Retrieval and Context Management

To enhance the realism and continuity of conversations, our web architecture includes a system for retrieving and utilizing chat history between a user and an AI character. This history serves as context for the LLM when generating responses, allowing the AI to "remember" previous interactions and respond accordingly.

### Key Components of Chat History Retrieval and Context Management:

1. Chat History Retrieval
2. Context Processing
3. LLM Integration
4. Privacy and Boundary Enforcement

Additionally, you can read about implementation examples and considerations on optimization of Chat History Retrieval and Context Management.

### 1. Chat History Retrieval

When a user initiates a chat or sends a new message, the backend API retrieves the relevant chat history from the database.

```python
from sqlalchemy.orm import Session
from sqlalchemy import and_
from . import models

def get_chat_history(db: Session, user_id: int, character_id: int, limit: int = 50):
    return db.query(models.ChatMessage).filter(
        and_(
            models.ChatMessage.user_id == user_id,
            models.ChatMessage.character_id == character_id
        )
    ).order_by(models.ChatMessage.created_at.desc()).limit(limit).all()
```

### 2. Context Processing

The retrieved chat history is processed and formatted to provide context for the LLM.

```python
def format_chat_history(chat_messages):
    formatted_history = []
    for msg in reversed(chat_messages):  # Reverse to get chronological order
        formatted_history.append(f"User: {msg.message}")
        formatted_history.append(f"AI: {msg.response}")
    return "\n".join(formatted_history)
```

### 3. LLM Integration

The formatted chat history is included in the prompt sent to the LLM service.

```python
def generate_ai_response(llm_service, user_message, character_id, chat_history):
    prompt = f"""
    Chat History:
    {chat_history}

    Current conversation:
    User: {user_message}
    AI:
    """
    return llm_service.generate_response(prompt, character_id)
```

### 4. Privacy and Boundary Enforcement

It's crucial to ensure that only relevant chat history is included. The system must not include:
- Chats between the same user and other AI characters
- Chats between the same AI character and other users

This is enforced by the SQL query in the `get_chat_history` function, which filters by both `user_id` and `character_id`.

### Implementation in API Endpoint

```python
@app.post("/api/chat")
def chat(chat_request: schemas.ChatRequest, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id=chat_request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Retrieve chat history
    chat_history = get_chat_history(db, chat_request.user_id, chat_request.character_id)
    formatted_history = format_chat_history(chat_history)
    
    # Generate response using LLM service with chat history context
    response = generate_ai_response(llm_service, chat_request.message, chat_request.character_id, formatted_history)
    
    # Save new message and response to database
    crud.create_chat_message(db, user_id=chat_request.user_id, character_id=chat_request.character_id,
                             message=chat_request.message, response=response)
    
    return {"message": response}
```

### Considerations and Optimizations

1. **Performance**: Retrieving and processing chat history for each message can be resource-intensive. Consider implementing caching mechanisms to store recent chat history between a logged-in user and the AI character they are talking to.

2. **Context Length**: LLMs often require more resources with longer contexts. Keep in mind that if some users will be really addicted and they have a long history with an AI character, we may eventually need to improve our architecture with vector DBs in order to implement more efficient RAG methods.

3. **Relevance and User Experience**: As conversations grow longer, older messages may become less relevant. Consider implementing a relevance scoring system to prioritize more recent or significant interactions. We can also optimize and improve the experience at the same time, since humans also 'forget' earlier conversations. If the AI is prompted by the user with something like 'you should remember this', more of the chat history can be included into the context.

### Summary of Chat History Retrieval and Context Management

By incorporating this chat history retrieval and context management system, our LLM chat service can provide more coherent, contextualized, and personalized interactions, significantly enhancing the user experience and the perceived intelligence of the AI characters.

## Conclusion

This web architecture provides a scalable, secure, and efficient foundation for our LLM-based chat service. By separating concerns between the frontend, backend API, and LLM service, we maintain flexibility and ease of development. The inclusion of caching, load balancing, and the potential for multiple model support ensures that our service can grow and adapt to future needs.