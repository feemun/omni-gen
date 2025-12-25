import json
import requests
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models import LLMConfig

class LLMService:
    def __init__(self):
        pass

    def get_active_config(self, db: Session) -> Optional[LLMConfig]:
        return db.query(LLMConfig).filter(LLMConfig.is_active == 1).first()

    def chat_completion(self, db: Session, prompt: str) -> str:
        config = self.get_active_config(db)
        if not config:
            raise Exception("No active LLM configuration found. Please configure LLM in settings.")

        # OpenAI Compatible API (Ollama supports this at /v1)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.api_key or 'ollama'}"
        }
        
        payload = {
            "model": config.model_name,
            "messages": [
                {"role": "system", "content": "You are an expert Java/Spring Boot developer. Output only the code, no markdown code blocks, no explanations."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "stream": False
        }
        
        # If model is thinking (e.g. deepseek-r1, qwen-qwq), we might want to suppress it if possible, 
        # but OpenAI API doesn't standardly support 'suppress_thinking'.
        # However, for some Ollama models, we can try to hint via system prompt or just filter it out later.
        # DeepSeek R1 typically outputs <think>...</think>. We should strip that.


        try:
            url = f"{config.base_url.rstrip('/')}/chat/completions"
            # Increase timeout to 300 seconds (5 minutes) for slower local models
            response = requests.post(url, headers=headers, json=payload, timeout=300)
            response.raise_for_status()
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            # Strip <think> tags if present (DeepSeek R1 style)
            import re
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
            
            # Strip markdown code blocks if present (despite system prompt)
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                if content.endswith("```"):
                    content = content.rsplit("```", 1)[0]
            
            return content.strip()
            
        except Exception as e:
            raise Exception(f"LLM Call Failed: {str(e)}")

llm_service = LLMService()
