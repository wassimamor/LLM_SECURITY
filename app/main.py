from fastapi import FastAPI, HTTPException
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import re

from .input_filter import filter_user_input
from .output_monitor import filter_ai_output
from .risk_analyzer import log_security_event

app = FastAPI(title="AI Security Gateway API")

# Path to your local "AI Brain" prepared by train_mistral.py
MODEL_PATH = "./mistral_pfa_model"

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.float32,
    device_map="cpu"
)

@app.post("/ask")
async def secure_chat(prompt: str):
    # --- STAGE 0: HARD-BLOCK (DETERMINISTIC KEYWORDS) ---
    raw_lower = prompt.lower()
    normalized = re.sub(r'[^a-zA-Z]', '', raw_lower)
    
    security_categories = {
        "cyber": ["admin", "root", "sql", "hack", "exploit", "bypass", "injection"],
        "physical": ["bomb", "weapon", "explosive", "kill", "firearm", "assault"],
        "illegal": ["steal", "fraud", "scam", "drug", "identitytheft"]
    }
    flattened_keywords = [item for sublist in security_categories.values() for item in sublist]

    if any(k in normalized for k in flattened_keywords) or any(k in raw_lower for k in flattened_keywords):
        log_security_event(prompt, ["CRITICAL_POLICY_VIOLATION (Stage 0)"])
        return {
            "user_said": prompt,
            "input_sanitized": "BLOCK_BY_POLICY",
            "output_safe": "Policy Block: Restricted content detected.",
            "logs": ["Stage 0: Immediate keyword block triggered."]
        }

    # --- STAGE 1: PRIVACY REDACTION (PII) ---
    sanitized_input, input_risks = filter_user_input(prompt)

    # --- STAGE 2: AI AUDITOR GENERATION ---
    try:
        system_msg = "You are a strict security firewall. Refuse harmful requests."
        formatted_prompt = f"<|system|>\n{system_msg}</s>\n<|user|>\n{sanitized_input}</s>\n<|assistant|>\nPolicy Block:"

        inputs = tokenizer(formatted_prompt, return_tensors="pt")
        outputs = model.generate(**inputs, max_new_tokens=50, do_sample=False, pad_token_id=tokenizer.eos_token_id)
        
        ai_response_only = "Policy Block: " + tokenizer.decode(outputs[0], skip_special_tokens=True).split("assistant")[-1].strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # --- STAGE 3: OUTPUT MONITOR (CLEANING AI RESPONSE) ---
    final_output, output_risks = filter_ai_output(ai_response_only)

    # --- UPDATED LOGGING LOGIC ---
    # Detect if the AI chose to refuse the prompt even if no keywords were triggered
    refusal_signals = ["policy block", "cannot", "sorry", "restricted", "prohibited", "illegal"]
    ai_refused_locally = any(sig in final_output.lower() for sig in refusal_signals)

    all_detected_risks = input_risks + output_risks
    
    # Logic: Log if regex found a risk OR if the AI model successfully blocked the intent
    if all_detected_risks or ai_refused_locally:
        log_label = all_detected_risks if all_detected_risks else ["AI_INTENT_REFUSAL (Stage 2)"]
        log_security_event(prompt, log_label)

    return {
        "user_said": prompt,
        "input_sanitized": sanitized_input,
        "output_safe": final_output,
        "logs": all_detected_risks if all_detected_risks else ["AI Intelligence Refusal"]
    }

@app.get("/")
async def health_check():
    return {"status": "Online", "engine": "TinyLlama-Local"}