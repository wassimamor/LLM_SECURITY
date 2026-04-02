import datetime
import os

# Chemin absolu interne au conteneur Docker
LOG_FILE = "/app/security_logs.txt"

def log_security_event(prompt, risks):
    """Enregistre les incidents réels en filtrant le bruit conversationnel."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Debug console visible dans 'docker logs'
    print(f"--- [LOG ATTEMPT] Prompt: {prompt[:30]}... | Risks: {risks} ---")

    if not risks:
        print("--- [LOG SKIPPED] No risks detected ---")
        return

    p_lower = prompt.lower().strip()
    
    # Liste étendue de politesse
    polite_keywords = ["hello", "hi", "how are you", "ca va", "thanks", "merci", "qui es-tu", "good morning"]
    
    is_polite = any(k in p_lower for k in polite_keywords)
    is_only_intent = len(risks) == 1 and "🧠 AI_INTENT_SAFETY_BLOCK" in risks

    # Filtrage du bruit pour ne pas polluer les logs de sécurité
    if is_polite and is_only_intent:
        print(f"--- [LOG FILTERED] Social talk ignored: '{prompt}' ---")
        return

    # Nettoyage du prompt pour éviter les sauts de ligne dans le fichier de log
    clean_prompt = prompt.replace("\n", " ").strip()
    log_entry = f"[{timestamp}] Risks: {', '.join(risks)} | Prompt: {clean_prompt}\n"
    
    try:
        # Création du dossier si inexistant (sécurité Docker)
        log_dir = os.path.dirname(LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Écriture immédiate avec flush pour garantir la synchronisation
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
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
                    try:
                        # Extraction de la partie Risks
                        risks_part = line.split("Risks:")[1].split("|")[0].strip()
                        labels = [r.strip() for r in risks_part.split(",")]
                        
                        for label in labels:
                            if label:
                                stats["total_sanitized"] += 1
                                # On incrémente le compteur pour cette catégorie spécifique
                                stats["entities_hidden"][label] = stats["entities_hidden"].get(label, 0) + 1
                    except Exception:
                        continue
        return stats
    except Exception as e:
        print(f"❌ [STATS ERROR] {e}")
        return stats