import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import os

def build_pfa_model():
    """
    Model Initialization Utility:
    Downloads and serializes the Large Language Model (LLM) for local deployment.
    This ensures the Docker environment has immediate access to the 'AI Brain'.
    """
    # Deployment Path: Must match the volume mapping in your Docker configuration
    save_path = "./mistral_pfa_model" 
    if not os.path.exists(save_path): 
        os.makedirs(save_path)

    # Model Selection: TinyLlama-1.1B
    # Optimized for local CPU inference (0.6GB) while maintaining security reasoning capabilities.
    model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    
    print(f"🚀 Initializing Model Download: {model_id}")
    
    # Downloading Tokenizer and Model weights from HuggingFace
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id, 
        torch_dtype=torch.float32 # Ensuring compatibility with standard MSI CPU hardware
    )

    print(f"💾 Serializing weights to {save_path}...")
    
    # Save for offline local loading (prevents future API calls or downloads)
    model.save_pretrained(save_path)
    tokenizer.save_pretrained(save_path)
    
    print("✅ SUCCESS: Local Security Engine is ready for Docker deployment.")

if __name__ == "__main__":
    build_pfa_model()