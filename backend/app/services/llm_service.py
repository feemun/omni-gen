import json
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models import LLMConfig
from openai import OpenAI

class LLMService:
    def __init__(self):
        pass

    def get_active_config(self, db: Session) -> Optional[LLMConfig]:
        return db.query(LLMConfig).filter(LLMConfig.is_active == 1).first()

    def chat_completion(self, db: Session, prompt: str) -> str:
        config = self.get_active_config(db)
        if not config:
            raise Exception("No active LLM configuration found. Please configure LLM in settings.")

        # Prepare client
        api_key = config.api_key
        if not api_key:
            if config.provider == "ollama":
                api_key = "ollama"
            else:
                # Strictly require API Key for other providers (DeepSeek, OpenAI, etc)
                raise Exception(f"API Key is required for provider {config.provider}. Please configure it in settings.") 

        # Clean base_url
        # OpenAI client expects "https://api.deepseek.com" or "http://localhost:11434/v1"
        # It appends /chat/completions itself
        base_url = config.base_url.strip().rstrip('/')
        if base_url.endswith("/chat/completions"):
            base_url = base_url.replace("/chat/completions", "")
        
        print(f"DEBUG: Initializing OpenAI Client with base_url='{base_url}', model='{config.model_name}'")

        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=600.0 # Set timeout to 10 minutes for long generations
        )

        try:
            # DeepSeek / OpenAI Call
            response = client.chat.completions.create(
                model=config.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert Java/Spring Boot developer. Output only the code, no markdown code blocks, no explanations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                stream=False
            )
            
            content = response.choices[0].message.content
            
            # Strip <think> tags if present (DeepSeek R1 style)
            import re
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
            
            # Strip markdown code blocks if present
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                if content.endswith("```"):
                    content = content.rsplit("```", 1)[0]
            
            return content.strip()
            
        except Exception as e:
            raise Exception(f"LLM Call Failed: {str(e)}")

llm_service = LLMService()
