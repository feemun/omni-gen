from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

class DatabaseConfig(Base):
    __tablename__ = "database_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    type = Column(String, default="mysql") # mysql, postgresql, sqlite
    
    host = Column(String, nullable=True)
    port = Column(Integer, nullable=True)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)
    database_name = Column(String, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    @property
    def url(self):
        if self.type == 'sqlite':
            return f"sqlite:///{self.database_name}"
        if not all([self.host, self.port, self.username, self.database_name]):
            return ""
        if self.type == 'mysql':
            return f"mysql+pymysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database_name}"
        elif self.type == 'postgresql':
            return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database_name}"
        return ""

class RedisConfig(Base):
    __tablename__ = "redis_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    
    host = Column(String, nullable=False, default="localhost")
    port = Column(Integer, nullable=False, default=6379)
    password = Column(String, nullable=True)
    db_index = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class ESConfig(Base):
    __tablename__ = "es_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    
    hosts = Column(String, nullable=False) # Comma separated list of hosts
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class TemplateGroup(Base):
    __tablename__ = "template_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    templates = relationship("Template", back_populates="group", cascade="all, delete-orphan")

class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("template_groups.id"), nullable=True) # Optional for now, or force assignment
    
    name = Column(String, index=True)  # Template filename/path (e.g., "entity.java.jinja2")
    display_name = Column(String, default="")       # User friendly name
    prompt = Column(String, default="")             # LLM Prompt
    content = Column(String, nullable=False)        # Template content
    
    root_path = Column(String, default="")          # Root directory
    relative_path = Column(String, default="")      # Relative path pattern (e.g. {{TableName}}.java)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    group = relationship("TemplateGroup", back_populates="templates")

class LLMConfig(Base):
    __tablename__ = "llm_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)               # Config name (e.g. "Local Ollama")
    provider = Column(String, default="ollama")     # "ollama" or "openai_compatible"
    base_url = Column(String, nullable=False)       # e.g. "http://localhost:11434/v1"
    api_key = Column(String, nullable=True)         # API Key (optional for Ollama)
    model_name = Column(String, nullable=False)     # e.g. "llama3", "gpt-4"
    is_active = Column(Integer, default=0)          # 1 for active, 0 for inactive (using Integer for boolean behavior in SQLite simple compat)
    created_at = Column(DateTime, default=datetime.utcnow)

# App internal database
SQLALCHEMY_DATABASE_URL = "postgresql://user_TnPSGF:password_tnPdJH@10.0.0.6:5432/ai_code_gena"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
