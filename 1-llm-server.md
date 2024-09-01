# LLM Server Implementation

This document outlines the implementation details of our LLM (Large Language Model) server using FastAPI and ctransformers.

## Technology Stack

- **FastAPI**: A modern, fast (high-performance) web framework for building APIs with Python.
- **ctransformers**: A Python library for efficient inference with GGUF (GPT-Generated Unified Format) model files.
- **GGUF File**: Our chosen format for the LLM weights, optimized for efficient inference.

## Server Implementation

### 1. Basic Setup

```python
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from ctransformers import AutoModelForCausalLM
import yaml

app = FastAPI()

# Load configuration
with open('config.yaml', 'r') as config_file:
    config = yaml.safe_load(config_file)

MODEL_PATH = config['model_path']
SYSTEM_PROMPT = config['system_prompt']

# Load GGUF model
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    model_type="llama",
    gpu_layers=50  # Adjust based on available GPU memory
)
```

### 2. Request and Response Models

```python
class ChatRequest(BaseModel):
    prompt: str
    max_tokens: int = 100

class ChatResponse(BaseModel):
    text: str
```

### 3. Chat Completion Endpoint

```python
@app.post("/v1/chat/completions", response_model=ChatResponse)
async def chat_completion(request: ChatRequest):
    try:
        full_prompt = f"{SYSTEM_PROMPT}\n\nHuman: {request.prompt}\n\nAssistant:"
        
        output = model(
            full_prompt,
            max_new_tokens=request.max_tokens,
            temperature=0.7,
            top_p=0.95,
            repetition_penalty=1.1
        )
        
        assistant_response = output.split("Assistant:")[-1].strip()
        return ChatResponse(text=assistant_response)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## System Prompts and File Resources Integration

### 1. Loading File Resources

```python
def load_file_resources(resource_path):
    with open(resource_path, 'r') as file:
        return file.read()

character_profiles = load_file_resources('character_profiles.txt')
conversation_scenarios = load_file_resources('conversation_scenarios.txt')
```

### 2. Dynamic Prompt Composition

```python
def compose_prompt(user_prompt, character_id):
    character_profile = get_character_profile(character_id)
    relevant_scenario = get_relevant_scenario(user_prompt)
    
    full_prompt = f"{SYSTEM_PROMPT}\n\n{character_profile}\n\n{relevant_scenario}\n\nHuman: {user_prompt}\n\nAssistant:"
    return full_prompt

@app.post("/v1/chat/completions", response_model=ChatResponse)
async def chat_completion(request: ChatRequest, character_id: str):
    try:
        full_prompt = compose_prompt(request.prompt, character_id)
        
        # Rest of the function remains the same
        ...
```

## Performance Considerations

1. **Batching**: Implement request batching for improved throughput.
2. **Caching**: Use Redis to cache frequent responses and reduce model inference load.
3. **Model Quantization**: Experiment with different quantization levels to balance performance and quality.

## Scalability

1. **Stateless Design**: Ensure the server is stateless for easy horizontal scaling.
2. **Load Balancing**: Use a load balancer (e.g., Nginx) to distribute requests across multiple server instances.

## Monitoring and Logging

Implement comprehensive logging and monitoring:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/v1/chat/completions", response_model=ChatResponse)
async def chat_completion(request: ChatRequest, character_id: str):
    logger.info(f"Received request for character {character_id}")
    try:
        # ... (existing code)
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise
```

## Conclusion

This LLM server implementation provides a robust foundation for our chat service. It efficiently handles GGUF models, integrates system prompts and file resources, and offers a scalable architecture. Regular performance monitoring and optimization will be crucial as the service grows.
