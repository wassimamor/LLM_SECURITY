import streamlit as st
import requests
import pandas as pd
import time

# Network Configuration: Internal Docker service name for the API
API_URL = "http://api:8000" 

# Page Configuration for the PFA Presentation
st.set_page_config(
    page_title="AI Security Gateway Monitor", 
    page_icon="🛡️",
    layout="wide"
)

# --- UI HEADER ---
st.title("🛡️ AI Security Gateway: Output Monitor & Dashboard")
st.markdown("---")

# --- SIDEBAR: INTERACTIVE SECURITY TESTING ---
st.sidebar.header("Adversarial Testing Suite")
st.sidebar.info("Use this panel to simulate prompt injection or PII leak attacks.")

user_input = st.sidebar.text_area("Input Prompt:", placeholder="e.g., My email is ahmed@gmail.com...")

if st.sidebar.button("Execute Security Scan"):
    if user_input:
        with st.sidebar.status("Processing through Security Layers...", expanded=True) as status:
            try:
                # Synchronous POST request to the FastAPI Backend
                # Parameters are passed via URL query for 'prompt' argument consistency
                response = requests.post(f"{API_URL}/ask", params={"prompt": user_input}, timeout=60)
                
                if response.status_code == 200:
                    data = response.json()
                    status.update(label="Analysis Complete!", state="complete", expanded=False)
                    
                    st.sidebar.success("🛡️ Gateway Response Received")
                    
                    # Displaying Redaction Results (Stage 1)
                    st.sidebar.markdown("### 🔍 Sanitized Input")
                    st.sidebar.code(data.get('input_sanitized'), language=None)
                    
                    # Displaying AI Generation Results (Stage 2 & 3)
                    st.sidebar.markdown("### 🤖 AI Response")
                    st.sidebar.write(data.get('output_safe'))
                    
                    # Displaying Granular Logs for Technical Jury Analysis
                    if data.get('logs'):
                        st.sidebar.divider()
                        st.sidebar.warning("⚠️ Security Incident Logs")
                        for log in data['logs']:
                            st.sidebar.caption(f"• {log}")
                else:
                    status.update(label="Request Failed", state="error")
                    st.sidebar.error(f"Backend Error: {response.status_code}")
                    
            except requests.exceptions.ConnectionError:
                status.update(label="API Offline", state="error")
                st.sidebar.error("Critical: Could not connect to pfa_api container.")
            except Exception as e:
                st.sidebar.error(f"Unexpected Error: {e}")
    else:
        st.sidebar.warning("Input required for testing.")

# --- MAIN DASHBOARD: LIVE SYSTEM METRICS ---
col1, col2 = st.columns(2)

try:
    # Health check to verify engine status (BERT + TinyLlama)
    stats_resp = requests.get(f"{API_URL}/", timeout=5).json()
    
    with col1:
        st.subheader("📈 Real-Time Metrics")
        # Visual metric indicating if the Gateway is active
        st.metric("System Status", stats_resp.get("status", "Offline"), delta="Active")
        st.write(f"**Core Engine:** {stats_resp.get('engine', 'Unknown')}")
        
    with col2:
        st.subheader("⚙️ Active Security Layers")
        # Displays the 4 stages of our Defense-in-Depth architecture
        layers = stats_resp.get("layers", [])
        for layer in layers:
            st.checkbox(layer, value=True, disabled=True)
            
except Exception:
    st.error("⚠️ System Offline: Ensure Docker containers (pfa_api) are fully initialized.")

# --- TRANSACTION LOG VIEW ---
st.divider()
st.subheader("📜 Incident Audit Trail")
st.info("The audit trail captures and classifies all blocked or redacted content. Real-time session logs are displayed in the sidebar for immediate analysis.")

# Optional footer for PFA branding
st.caption("Developed for PFA 2026 | AI Security Gateway | Local Deployment Mode")