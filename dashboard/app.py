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

# Timeout augmenté à 120s pour laisser le temps au CPU de traiter les gros prompts
if st.sidebar.button("Execute Scan"):
    if user_input:
        with st.sidebar.status("Analyzing through security layers...", expanded=False):
            try:
                response = requests.post(f"{API_URL}/ask", params={"prompt": user_input}, timeout=120)
                if response.status_code == 200:
                    data = response.json()
                    st.sidebar.success("Analysis Complete")
                    
                    # Affichage des alertes dans la sidebar
                    classifications = data.get('security_classification', [])
                    for label in classifications:
                        if "✅" in label: 
                            st.sidebar.info(label)
                        else: 
                            st.sidebar.error(f"DETECTION: {label}")
                    
                    st.sidebar.divider()
                    st.sidebar.markdown("### 🤖 AI Output")
                    st.sidebar.write(data.get('output_safe', ""))
            except Exception as e:
                st.sidebar.error(f"Error: {e}")

# --- MAIN DASHBOARD: MÉTRIQUES SYSTÈME ---
st.subheader("📊 Security Infrastructure Analytics")
col1, col2, col3 = st.columns(3)

try:
    # Récupération des infos de santé
    stats_resp = requests.get(f"{API_URL}/", timeout=5).json()
    
    with col1:
        st.metric("Gateway Status", "ACTIVE", delta="Secure")
        st.caption(f"Engine: {stats_resp.get('engine', 'Mistral')}")
        
    with col2:
        st.write("**Active Defense Layers:**")
        # Récupère dynamiquement la liste définie dans main.py
        for layer in stats_resp.get("layers", []):
            st.markdown(f"✅ `{layer}`")

    with col3:
        st.write("**System Integrity:**")
        st.info("Logs are strictly persisted to `security_logs.txt` for forensic audit.")

except Exception:
    st.error("⚠️ Connection to Security Engine lost.")

# --- SECTION VISUELLE : RÉCUPÉRATION DES STATS RÉELLES ---
st.divider()
st.subheader("📈 Attack Distribution (Categorized)")

try:
    # APPEL AU NOUVEAU ENDPOINT /stats
    res_stats = requests.get(f"{API_URL}/stats", timeout=5)
    
    if res_stats.status_code == 200:
        actual_stats = res_stats.json()
        entities = actual_stats.get("entities_hidden", {})

        if entities:
            # On transforme le dictionnaire JSON en DataFrame pour le graphique
            df = pd.DataFrame({
                "Category": list(entities.keys()),
                "Count": list(entities.values())
            })
            
            # Affichage du graphique réel
            st.bar_chart(df, x="Category", y="Count", color="#ff4b4b")
            
            # Petit tableau récapitulatif pour le jury
            with st.expander("Show detailed count table"):
                st.table(df)
        else:
            st.info("No attacks detected yet. The graph will update automatically after a detection.")
    else:
        st.warning("Could not sync statistics with the log file.")

except Exception as e:
    st.caption(f"Waiting for real-time data sync... (Status: {e})")

st.divider()
st.caption("Note: Raw logs are hidden from the dashboard for security. Check `security_logs.txt` on the server.")

# Footer
st.divider()
st.caption("Developed for PFA 2026 | Sfax, Tunisia")