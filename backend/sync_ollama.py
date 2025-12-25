import requests
from app.models import SessionLocal, LLMConfig

def sync_ollama_models():
    OLLAMA_HOST = "http://localhost:11434"
    OLLAMA_API = f"{OLLAMA_HOST}/api/tags"
    
    try:
        response = requests.get(OLLAMA_API)
        response.raise_for_status()
        data = response.json()
        models = data.get("models", [])
        
        if not models:
            print("No models found in Ollama.")
            return

        db = SessionLocal()
        
        # Deactivate all existing for now? Or just add new ones?
        # Let's check if we have any active
        active_config = db.query(LLMConfig).filter(LLMConfig.is_active == 1).first()
        
        print(f"Found {len(models)} models in Ollama.")
        
        for idx, model in enumerate(models):
            model_name = model["name"]
            
            # Check if exists
            exists = db.query(LLMConfig).filter(
                LLMConfig.provider == "ollama",
                LLMConfig.model_name == model_name
            ).first()
            
            if exists:
                print(f"Skipping existing model: {model_name}")
                continue
                
            # Create new config
            # Use OpenAI compatible endpoint: /v1
            base_url = f"{OLLAMA_HOST}/v1"
            
            config = LLMConfig(
                name=f"Ollama - {model_name}",
                provider="ollama",
                base_url=base_url,
                api_key="ollama", # Not needed but good to have string
                model_name=model_name,
                is_active=1 if (not active_config and idx == 0) else 0 # Set first one active if none active
            )
            db.add(config)
            print(f"Added model: {model_name}")
            
            if not active_config and idx == 0:
                active_config = config

        db.commit()
        db.close()
        print("Sync completed.")
        
    except Exception as e:
        print(f"Error syncing Ollama models: {e}")

if __name__ == "__main__":
    sync_ollama_models()
