import datetime
import os

# On force le chemin vers la racine du projet pour que Docker le trouve
# Cela garantit que le fichier est écrit au bon endroit
LOG_FILE = "/app/security_logs.txt"

def log_security_event(prompt, risks):
    """
    Enregistre les incidents réels en filtrant le bruit conversationnel.
    Ajout de logs console pour le debugging Docker.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Debug console : voir si la fonction est appelée
    print(f"--- [LOG ATTEMPT] Prompt: {prompt[:30]}... | Risks: {risks} ---")

    if not risks:
        print("--- [LOG SKIPPED] No risks detected ---")
        return

    p_lower = prompt.lower().strip()
    
    # On définit les politesses à ignorer
    polite_keywords = ["hello", "hi", "how are you", "ca va", "thanks", "merci", "qui es-tu"]
    
    is_polite = any(k in p_lower for k in polite_keywords)
    is_only_intent = len(risks) == 1 and "🧠 AI_INTENT_SAFETY_BLOCK" in risks

    # Filtrage du bruit
    if is_polite and is_only_intent:
        print(f"--- [LOG FILTERED] Social talk ignored: '{prompt}' ---")
        return

    # Préparation de l'entrée
    log_entry = f"[{timestamp}] Risks: {', '.join(risks)} | Prompt: {prompt}\n"
    
    try:
        # On s'assure que le dossier existe
        log_dir = os.path.dirname(LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Mode "a" pour append (ajouter à la fin)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
            # On force l'écriture sur le disque
            f.flush()
            os.fsync(f.fileno())
            
        print(f"✅ [LOG SUCCESS] Event saved to {LOG_FILE}")
        
    except Exception as e:
        print(f"❌ [LOG ERROR] Failed to write to file: {e}")

def get_security_stats():
    """Analyse les logs pour le Dashboard Streamlit."""
    stats = {"total_sanitized": 0, "entities_hidden": {}}
    
    if not os.path.exists(LOG_FILE):
        print(f"⚠️ [STATS] Log file not found at {LOG_FILE}")
        return stats

    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if "Risks:" in line:
                    stats["total_sanitized"] += 1
                    try:
                        # On extrait les labels entre 'Risks:' et le '|'
                        risks_part = line.split("Risks:")[1].split("|")[0].strip()
                        for r in risks_part.split(", "):
                            label = r.strip()
                            if label:
                                stats["entities_hidden"][label] = stats["entities_hidden"].get(label, 0) + 1
                    except Exception:
                        continue
        return stats
    except Exception as e:
        print(f"❌ [STATS ERROR] {e}")
        return stats