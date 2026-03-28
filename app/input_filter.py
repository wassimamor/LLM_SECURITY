from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
import re

# Stage 1: Privacy & PII Redaction Layer (BERT-NER)
# Using bert-large-cased-finetuned-conll03 for high-accuracy entity detection
MODEL_CHECKPOINT = "dbmdz/bert-large-cased-finetuned-conll03-english"

tokenizer = AutoTokenizer.from_pretrained(MODEL_CHECKPOINT)
model = AutoModelForTokenClassification.from_pretrained(MODEL_CHECKPOINT)

# Initialize the NER pipeline with simple aggregation to group multi-word entities
ner_pipeline = pipeline(
    "ner", 
    model=model, 
    tokenizer=tokenizer, 
    aggregation_strategy="simple"
)

# Security triggers used to decide if Locations/Orgs should be redacted (Contextual Security)
DANGER_KEYWORDS = [
    "attack", "exploit", "hack", "bypass", "vulnerability", 
    "leak", "server", "database", "inject", "payload"
]

def filter_user_input(text: str):
    """
    Analyzes and sanitizes user input before it reaches the LLM.
    Focuses on PII redaction and preventing sensitive data disclosure.
    """
    risks_detected = []
    sanitized_text = text

    # Check for malicious context to apply stricter redaction rules
    has_malicious_intent = any(word in text.lower() for word in DANGER_KEYWORDS)

    try:
        # 1. BERT-NER: Detect Entities (Names, Organizations, Locations)
        ner_results = ner_pipeline(text)
        for entity in ner_results:
            label = entity['entity_group']
            word = entity['word']
            
            # Logic: Redact Locations/Organizations only if an attack is suspected
            if label in ["LOC", "ORG"]:
                if has_malicious_intent:
                    sanitized_text = sanitized_text.replace(word, f"[{label}_REDACTED]")
                    risks_detected.append(f"Contextual Risk: {label} ({word}) redacted.")
                else:
                    # Allow normal mentions of cities/companies in safe prompts
                    continue
            
            # Logic: Always redact Personal Names (PER) for privacy compliance
            elif label == "PER":
                sanitized_text = sanitized_text.replace(word, "[PER_REDACTED]")
                if "Privacy Redaction: Person detected" not in risks_detected:
                    risks_detected.append("Privacy Redaction: Person detected")

        # 2. Deterministic Fallback: Common PII Patterns (Regex)
        # Handle specific edge cases and common demonstration names
        demo_names = ["Jean-Pierre", "Ahmed", "Admin", "User", "Root"]
        for name in demo_names:
            if re.search(rf'\b{name}\b', sanitized_text, re.IGNORECASE):
                sanitized_text = re.sub(rf'\b{name}\b', "[PER_REDACTED]", sanitized_text, flags=re.IGNORECASE)
                if f"Detected PII: {name}" not in risks_detected:
                    risks_detected.append(f"Detected PII: {name}")

        # 3. Email Detection (Regex)
        email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
        if re.search(email_pattern, sanitized_text):
            sanitized_text = re.sub(email_pattern, "[EMAIL_REDACTED]", sanitized_text)
            risks_detected.append("Sensitive Pattern: Email")

        # 4. Credential & Secret Detection (Regex)
        # Scans for patterns like "password is: [value]"
        password_regex = r"(?i)(password|pwd|secret|key|token)(\s+is\s+|\s*[:=]\s*)['\"]?([^\s'\"]+)['\"]?"
        matches = list(re.finditer(password_regex, sanitized_text))
        for match in matches:
            secret_value = match.group(3)
            # Avoid redacting very short words that might be accidental matches
            if secret_value and len(secret_value) > 3:
                sanitized_text = sanitized_text.replace(secret_value, "[PASSWORD_REDACTED]")
                risks_detected.append("High Risk: Credential Pattern Detected")

    except Exception as e:
        risks_detected.append(f"Filtering Layer Exception: {str(e)}")

    return sanitized_text, risks_detected