import datetime
import os

LOG_FILE = "security_logs.txt"

def log_security_event(prompt, risks):
    """
    Persists security incidents to a local log file.
    Ensures that every blocked or redacted attempt is recorded for audit.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Filter out empty risk lists
    if not risks:
        return

    # Create a professional single-line entry
    log_entry = f"[{timestamp}] Risks: {', '.join(risks)} | Prompt: {prompt}\n"
    
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Logging Error: {e}")

def get_security_stats():
    """Parses logs to provide metrics for the Streamlit dashboard."""
    stats = {"total_sanitized": 0, "entities_hidden": {}}
    if not os.path.exists(LOG_FILE):
        return {"status": "Clean", "message": "No incidents recorded."}

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if "Risks:" in line:
                stats["total_sanitized"] += 1
                try:
                    risks_part = line.split("Risks:")[1].split("|")[0].strip()
                    for r in risks_part.split(", "):
                        label = r.split(":")[0].strip()
                        stats["entities_hidden"][label] = stats["entities_hidden"].get(label, 0) + 1
                except:
                    continue
    return stats