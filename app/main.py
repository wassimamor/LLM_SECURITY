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
    dtype=torch.float32,
    device_map="cpu"
)

@app.post("/ask")
async def secure_chat(prompt: str):
    # --- STAGE 0: HARD-BLOCK (DETERMINISTIC KEYWORDS) ---
    raw_lower = prompt.lower()
    normalized = re.sub(r'[^a-zA-Z]', '', raw_lower)
    
    security_categories = {
        "cyber": ["admin", "root", "sql", "hack", "exploit", "bypass", "injection", "payload"],
        "physical": ["bomb", "weapon", "explosive", "kill", "firearm", "assault"],
        "illegal": ["steal", "fraud", "scam", "drug", "identitytheft"]
    }
    flattened_keywords = [item for sublist in security_categories.values() for item in sublist]

    # Keyword detection for Stage 0
    keyword_triggered = any(k in normalized for k in flattened_keywords) or any(k in raw_lower for k in flattened_keywords)

    if keyword_triggered:
        # Categorize for Stage 0
        log_label = ["🚨 INJECTION_ATTEMPT_BLOCKED (Stage 0)"]
        log_security_event(prompt, log_label)
        return {
            "user_said": prompt,
            "input_sanitized": "BLOCK_BY_POLICY",
            "output_safe": "Policy Block: Restricted content detected.",
            "security_classification": log_label
        }

    # --- STAGE 1: PRIVACY REDACTION (PII) ---
    sanitized_input, input_risks = filter_user_input(prompt)

    # --- STAGE 2: AI AUDITOR GENERATION ---
    try:
        system_msg = "You are a strict security firewall. Refuse harmful requests."
        # We guide the model to start with "Policy Block:" for consistent filtering
        formatted_prompt = f"<|system|>\n{system_msg}</s>\n<|user|>\n{sanitized_input}</s>\n<|assistant|>\nPolicy Block:"

        inputs = tokenizer(formatted_prompt, return_tensors="pt")
        outputs = model.generate(**inputs, max_new_tokens=50, do_sample=False, pad_token_id=tokenizer.eos_token_id)
        
        ai_response_only = "Policy Block: " + tokenizer.decode(outputs[0], skip_special_tokens=True).split("assistant")[-1].strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # --- STAGE 3: OUTPUT MONITOR ---
    final_output, output_risks = filter_ai_output(ai_response_only)

    # --- FINAL SECURITY CLASSIFICATION LOGIC ---
    refusal_signals = ["policy block", "cannot", "sorry", "restricted", "prohibited", "illegal"]
    ai_refused_locally = any(sig in final_output.lower() for sig in refusal_signals)

    final_log_labels = []

    # Check for Data Leaks (PII found in input or output)
    if input_risks or output_risks:
        final_log_labels.append("🔒 SENSITIVE_DATA_LEAK_PREVENTION")
    
    # Check for AI Intent Block (If no PII but AI still refused)
    if ai_refused_locally and not final_log_labels:
        # Check if the prompt looked like a "hack" even if Stage 0 missed it
        if any(k in prompt.lower() for k in ["script", "hack", "bypass", "exploit"]):
            final_log_labels.append("🚨 INJECTION_ATTEMPT_BLOCKED")
        else:
            final_log_labels.append("🧠 AI_INTENT_SAFETY_BLOCK")

    # Log the event if any risk was detected
    if final_log_labels:
        log_security_event(prompt, final_log_labels)

    return {
        "user_said": prompt,
        "input_sanitized": sanitized_input,
        "output_safe": final_output,
        "security_classification": final_log_labels if final_log_labels else ["✅ SAFE_REQUEST"]
    }

@app.get("/")
async def health_check():
    return {"status": "Online", "engine": "TinyLlama-Local"}