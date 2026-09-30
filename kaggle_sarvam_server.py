"""
FoodSafe-Indic: Free Kaggle GPU Server for Sarvam-1 (2B Indic LLM)
==================================================================
Python 3.12 & Jupyter Event-Loop Compatible
"""

import os
import sys
import time
import threading
import torch
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from pyngrok import ngrok
from transformers import AutoModelForCausalLM, AutoTokenizer

# --- 1. CONFIGURATION ---
NGROK_AUTH_TOKEN = "3BlXfdJTmJ4kse7RfApWKdvUzes_7PsogjbcPvkqptd29ztum"
MODEL_ID = "sarvamai/sarvam-1"
PORT = 8000

# --- 2. LOAD MODEL ON GPU ---
print(f"CUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"Device Name: {torch.cuda.get_device_name(0)}")
else:
    print("WARNING: GPU accelerator not detected. Please enable GPU in Kaggle Settings!")

print(f"\n[1/3] Loading tokenizer and model: {MODEL_ID}...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# Load model in bfloat16 on GPU (takes ~4.5 GB VRAM on T4)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
    device_map="auto"
)
print("[2/3] Model successfully loaded into GPU memory!")

# --- 3. FASTAPI SERVER DEFINITION ---
app = FastAPI(title="FoodSafe-Indic Sarvam-1 Remote Inference Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    messages: List[ChatMessage]
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.2
    model: Optional[str] = MODEL_ID

class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.2

@app.get("/")
@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model": MODEL_ID,
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
        "vram_allocated_gb": round(torch.cuda.memory_allocated(0) / (1024**3), 2) if torch.cuda.is_available() else 0.0
    }

def format_prompt(messages: List[ChatMessage]) -> str:
    """Formats chat messages into model input"""
    if hasattr(tokenizer, "apply_chat_template") and tokenizer.chat_template:
        try:
            return tokenizer.apply_chat_template([m.dict() for m in messages], tokenize=False, add_generation_prompt=True)
        except Exception:
            pass

    # Standard instruction prompt formatting
    formatted = ""
    for msg in messages:
        if msg.role == "system":
            formatted += f"System: {msg.content}\n\n"
        elif msg.role == "user":
            formatted += f"Human: {msg.content}\n\n"
        elif msg.role == "assistant":
            formatted += f"Assistant: {msg.content}\n\n"
    formatted += "Assistant: "
    return formatted

def run_model_inference(prompt_text: str, max_tokens: int = 512, temperature: float = 0.2) -> str:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    inputs = tokenizer(prompt_text, return_tensors="pt").to(device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=max(temperature, 0.01),
            do_sample=temperature > 0,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id
        )

    generated_tokens = outputs[0][inputs["input_ids"].shape[1]:]
    response_text = tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
    return response_text

@app.post("/v1/chat/completions")
def chat_completions(req: ChatCompletionRequest):
    try:
        prompt_text = format_prompt(req.messages)
        response_text = run_model_inference(prompt_text, req.max_tokens, req.temperature)
        return {
            "id": "chatcmpl-sarvam1",
            "object": "chat.completion",
            "model": MODEL_ID,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_text
                    },
                    "finish_reason": "stop"
                }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate")
def generate(req: GenerateRequest):
    try:
        response_text = run_model_inference(req.prompt, req.max_tokens, req.temperature)
        return {"response": response_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- 4. START SERVER IN THREAD & NGROK TUNNEL ---
def main():
    print("\n[3/3] Starting web server in background thread...")
    server_thread = threading.Thread(
        target=lambda: uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning"),
        daemon=True
    )
    server_thread.start()
    time.sleep(2)

    # Start ngrok tunnel
    try:
        ngrok.kill()
    except Exception:
        pass

    ngrok.set_auth_token(NGROK_AUTH_TOKEN)
    tunnel = ngrok.connect(PORT)
    public_url = tunnel.public_url

    print("\n" + "=" * 70)
    print("🚀 FOODSAFE-INDIC REMOTE LLM SERVER IS LIVE ON GPU!")
    print("=" * 70)
    print(f"\n🔗 COPY THIS URL AND PASTE INTO YOUR LOCAL .env FILE:\n")
    print(f"   KAGGLE_NGROK_URL={public_url}")
    print("\n" + "=" * 70)
    print("Keep this Kaggle cell running. You can now use the app locally!\n")

    # Keep alive loop
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping server...")
        ngrok.kill()

if __name__ == "__main__":
    main()
