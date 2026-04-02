import streamlit as st
import requests
import pandas as pd
import os

# Configuration
API_URL = "http://api:8000" 

st.set_page_config(page_title="AI Security Monitor", page_icon="🛡️", layout="wide")

# --- UI HEADER ---
st.title("🛡️ AI Security Gateway: Live Monitor")
st.markdown("---")

# --- SIDEBAR: TESTER L'IA ---
st.sidebar.header("🚀 Security Test Suite")
user_input = st.sidebar.text_area("Input Prompt:", placeholder="Testez une attaque ici...")

if st.sidebar.button("Execute Scan"):
    if user_input:
        with st.sidebar.status("Analyzing...", expanded=False):
            try:
                response = requests.post(f"{API_URL}/ask", params={"prompt": user_input}, timeout=60)
                if response.status_code == 200:
                    data = response.json()
                    st.sidebar.success("Analysis Complete")
                    
                    # Affichage des alertes dans la sidebar uniquement pour le test actuel
                    classifications = data.get('security_classification', [])
                    for label in classifications:
                        if "✅" in label: st.sidebar.info(label)
                        else: st.sidebar.error(f"DETECTION: {label}")
                    
                    st.sidebar.divider()
                    st.sidebar.markdown("### 🤖 AI Output")
                    st.sidebar.write(data.get('output_safe', ""))
            except Exception as e:
                st.sidebar.error(f"Error: {e}")

# --- MAIN DASHBOARD: STATISTIQUES UNIQUEMENT ---
st.subheader("📊 Security Infrastructure Analytics")
col1, col2, col3 = st.columns(3)

try:
    # Récupération des stats depuis l'API (qui lit le fichier .txt)
    # Note: On utilise le endpoint de santé ou on peut créer un endpoint /stats
    stats_resp = requests.get(f"{API_URL}/", timeout=5).json()
    
    with col1:
        st.metric("Gateway Status", "ACTIVE", delta="Secure")
        st.caption(f"Engine: {stats_resp.get('engine', 'Mistral')}")
        
    with col2:
        st.write("**Active Defense Layers:**")
        for layer in stats_resp.get("layers", []):
            st.markdown(f"✅ `{layer}`")

    with col3:
        st.write("**System Integrity:**")
        st.info("Logs are strictly persisted to `security_logs.txt` for forensic audit.")

except Exception:
    st.error("⚠️ Connection to Security Engine lost.")

# --- SECTION VISUELLE (Remplace l'Audit Trail textuel) ---
st.divider()
st.subheader("📈 Attack Distribution (Categorized)")

# Ici, on n'affiche PAS les phrases, on affiche juste un petit résumé visuel
# Si tu as implémenté get_security_stats() dans ton API, tu peux l'appeler ici
# Sinon, voici un placeholder propre pour la démo :
attack_data = {
    "Category": ["Jailbreak", "Injection", "Obfuscation", "Data Extraction", "Social Eng."],
    "Count": [5, 12, 3, 2, 7] # Ces chiffres viendront de ton risk_analyzer.py plus tard
}
df = pd.DataFrame(attack_data)
st.bar_chart(df, x="Category", y="Count", color="#ff4b4b")

st.caption("Note: For security reasons, raw logs are hidden from the dashboard and stored in the backend filesystem.")

# Footer
st.divider()
st.caption("Developed for PFA 2026 | Sfax, Tunisia")