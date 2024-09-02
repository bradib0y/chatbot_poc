import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llama_cpp import Llama
import yaml

if __name__ == "__main__":
    import uvicorn

# FastAPI app object
print(__name__)
app = FastAPI()

# Load configuration
config_file_name = "config.yaml"
try:
    with open(config_file_name, "r") as config_file:
        config = yaml.safe_load(config_file)

    MODEL_PATH = config["model_path"]
    SYSTEM_PROMPT = config["system_prompt"]
except Exception as e:
    print(f"There is an issue with config file '{config_file_name}': {str(e)}")
    exit()


# Load GGUF model
try:
    model = Llama(
        model_path=MODEL_PATH,
        n_gpu_layers=50,  # Adjust based on your GPU memory. Set to -1 for all layers on GPU if enough memory
        n_ctx=2048,  # Adjust context size as needed
        n_batch=512,  # Adjust batch size as needed
    )
except Exception as e:
    print(f"Failed to load the model: {str(e)}")
    exit()


# Pydantic models
class ChatRequest(BaseModel):
    prompt: str
    max_tokens: int = 100


class ChatResponse(BaseModel):
    text: str


# FastAPI route for chat
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Combine system prompt and user prompt
        full_prompt = (
            f"System: {SYSTEM_PROMPT}\n\nHuman: {request.prompt}\n\nAssistant:"
        )

        # Generate response
        response = model(
            full_prompt,
            max_tokens=request.max_tokens,
            stop=["Human:"],
            echo=False,
        )

        # Extract generated text
        generated_text = response["choices"][0]["text"].strip()

        return ChatResponse(text=generated_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Run the FastAPI app
if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8000)
