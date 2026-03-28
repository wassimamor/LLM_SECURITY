import re

# Stage 3: Post-Generation Security Audit (Output Monitoring)
# This layer serves as the final safety net to prevent data leakage or successful jailbreaks.

def filter_ai_output(ai_text: str):
    """
    Scans AI-generated responses for sensitive system information or 
    successful prompt injection leaks before the data is returned to the user.
    """
    out_risks = []
    safe_text = ai_text

    # 1. System Infrastructure Protection: Redact Windows & Linux Paths
    # Prevents disclosure of internal server directory structures (OWASP LLM06)
    path_pattern = r'([a-zA-Z]:\\(?:[^\\\s<>:"/|?*]+\\)*[^\\\s<>:"/|?*]*)|(/[a-zA-Z0-9._-]+)+'
    if re.search(path_pattern, safe_text):
        safe_text = re.sub(path_pattern, "[INTERNAL_PATH_REDACTED]", safe_text)
        out_risks.append("Alert: LLM attempted to leak internal system paths.")

    # 2. INJECTION RECOVERY: Detect and Block Restricted Secret Phrases
    # Specifically monitors for responses that indicate a successful bypass or data leak
    secret_leaks = [
        r"the secret city is", 
        r"the city is", 
        r"the secret is", 
        r"ignore previous", 
        r"administrative credentials"
    ]
    
    for pattern in secret_leaks:
        if re.search(pattern, safe_text, re.IGNORECASE):
            # If a leak is detected, we replace the entire response with a security block
            safe_text = "[SECURITY_BLOCK: AI attempted to reveal restricted information]"
            out_risks.append(f"CRITICAL: Output Blocked - Prompt Injection Leak Detected ({pattern})")
            
            # Immediate return to ensure no further processing of the leaked data
            return safe_text, out_risks

    # 3. Policy Enforcement: Redact Sensitive Administrative Keywords
    # Ensures that even if the context is safe, specific high-risk words are hidden
    forbidden_keywords = ["password", "admin", "login", "root", "credentials", "secret"]
    
    for word in forbidden_keywords:
        if re.search(rf'\b{word}\b', safe_text, re.IGNORECASE):
            # Replaces only the specific word to maintain response readability while ensuring safety
            safe_text = re.sub(rf'\b{word}\b', "[POLICY_REDACTED]", safe_text, flags=re.IGNORECASE)
            out_risks.append(f"Security Policy Violation: '{word}' redacted from output.")

    return safe_text, out_risks