from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.services.db_service import db_service
from app.services.generator_service import generator_service
from app.models import Base, DatabaseConfig, RedisConfig, ESConfig, Template, TemplateGroup, LLMConfig, engine, get_db, init_db
import uvicorn

# Initialize DB
init_db()

app = FastAPI(title="OmniGen API")

# CORS configuration
origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class ConnectRequest(BaseModel):
    db_url: str

class TableMetadataRequest(BaseModel):
    db_url: str
    table_name: str

class GenerateRequest(BaseModel):
    db_url: str
    selected_tables: List[str]
    template_group_id: int
    use_llm: bool = False

class DatabaseConfigCreate(BaseModel):
    name: str
    type: str = "mysql"
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    database_name: str

class DatabaseConfigResponse(BaseModel):
    id: int
    name: str
    type: str
    host: Optional[str]
    port: Optional[int]
    username: Optional[str]
    password: Optional[str]
    database_name: str
    url: str
    
    class Config:
        from_attributes = True

class RedisConfigCreate(BaseModel):
    name: str
    host: str = "localhost"
    port: int = 6379
    password: Optional[str] = None
    db_index: int = 0

class RedisConfigResponse(BaseModel):
    id: int
    name: str
    host: str
    port: int
    password: Optional[str]
    db_index: int
    
    class Config:
        from_attributes = True

class ESConfigCreate(BaseModel):
    name: str
    hosts: str
    username: Optional[str] = None
    password: Optional[str] = None

class ESConfigResponse(BaseModel):
    id: int
    name: str
    hosts: str
    username: Optional[str]
    password: Optional[str]
    
    class Config:
        from_attributes = True

class TemplateGroupCreate(BaseModel):
    name: str
    description: str = ""

class TemplateCreate(BaseModel):
    group_id: int
    name: str
    content: str
    root_path: str = ""
    relative_path: str = ""
    display_name: str = ""
    prompt: str = ""

class LLMConfigCreate(BaseModel):
    name: str
    provider: str
    base_url: str
    api_key: Optional[str] = None
    model_name: str
    is_active: bool = False

class LLMConfigResponse(BaseModel):
    id: int
    name: str
    provider: str
    base_url: str
    api_key: Optional[str]
    model_name: str
    is_active: bool
    
    class Config:
        from_attributes = True

# Template Group API
@app.post("/api/template-groups")
async def create_template_group(group: TemplateGroupCreate, db: Session = Depends(get_db)):
    db_group = TemplateGroup(name=group.name, description=group.description)
    db.add(db_group)
    try:
        db.commit()
        db.refresh(db_group)
        return db_group
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/template-groups")
async def get_template_groups(db: Session = Depends(get_db)):
    # Return groups with their templates
    groups = db.query(TemplateGroup).all()
    result = []
    for g in groups:
        result.append({
            "id": g.id,
            "name": g.name,
            "description": g.description,
            "templates": [
                {
                    "id": t.id, 
                    "name": t.name, 
                    "display_name": t.display_name,
                    "root_path": t.root_path,
                    "relative_path": t.relative_path
                } for t in g.templates
            ]
        })
    return result

@app.put("/api/template-groups/{id}")
async def update_template_group(id: int, group: TemplateGroupCreate, db: Session = Depends(get_db)):
    db_group = db.query(TemplateGroup).filter(TemplateGroup.id == id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    db_group.name = group.name
    db_group.description = group.description
    db.commit()
    db.refresh(db_group)
    return db_group

@app.delete("/api/template-groups/{id}")
async def delete_template_group(id: int, db: Session = Depends(get_db)):
    db_group = db.query(TemplateGroup).filter(TemplateGroup.id == id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    db.delete(db_group)
    db.commit()
    return {"ok": True}

# Template API
@app.get("/api/templates/{id}")
async def get_template_content(id: int, db: Session = Depends(get_db)):
    try:
        data = generator_service.get_template_content(db, id)
        return data
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/templates")
async def save_template(tmpl: TemplateCreate, db: Session = Depends(get_db)):
    try:
        generator_service.save_template(
            db, 
            tmpl.group_id,
            tmpl.name, 
            tmpl.content, 
            tmpl.root_path,
            tmpl.relative_path,
            tmpl.display_name,
            tmpl.prompt
        )
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/templates/{id}")
async def update_template(id: int, tmpl: TemplateCreate, db: Session = Depends(get_db)):
    try:
        # We reuse save_template logic but strictly it's an update. 
        # generator_service.save_template handles update if name matches, but here we reference by ID.
        # Let's refactor generator_service slightly or just update directly here for simplicity
        t = db.query(Template).filter(Template.id == id).first()
        if not t:
            raise HTTPException(status_code=404, detail="Template not found")
        
        t.group_id = tmpl.group_id
        t.name = tmpl.name
        t.content = tmpl.content
        t.root_path = tmpl.root_path
        t.relative_path = tmpl.relative_path
        t.display_name = tmpl.display_name
        t.prompt = tmpl.prompt
        db.commit()
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/templates/{id}")
async def delete_template(id: int, db: Session = Depends(get_db)):
    try:
        generator_service.delete_template(db, id)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ... (Connect DB API) ...

@app.post("/api/connect")
async def connect_db(request: ConnectRequest):
    try:
        tables = db_service.get_tables(request.db_url)
        return {"tables": tables}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/table-metadata")
async def get_table_metadata(request: TableMetadataRequest):
    try:
        schema = db_service.get_table_schema(request.db_url, request.table_name)
        return schema
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/generate")
async def generate_code(request: GenerateRequest, db: Session = Depends(get_db)):
    results = []
    try:
        # Get all templates in the group
        group = db.query(TemplateGroup).filter(TemplateGroup.id == request.template_group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="Template Group not found")
        
        if not group.templates:
             raise HTTPException(status_code=400, detail="No templates in this group")

        for table in request.selected_tables:
            schema = db_service.get_table_schema(request.db_url, table)
            
            table_files = []
            for tmpl in group.templates:
                code = generator_service.generate_code(db, tmpl.id, schema, request.use_llm)
                # Resolve output path
                # Simple variable substitution for output path (e.g. {{TableName}})
                # We can reuse jinja environment to render path too
                from jinja2 import Environment, DictLoader
                
                # We need a context for path rendering. Schema has 'TableName' usually?
                # db_service.get_table_schema returns dict with 'columns', but maybe we add 'TableName'?
                # Let's ensure schema has TableName
                context = schema.copy()
                context['TableName'] = table # Add table name if not present
                
                # Create env for path rendering (lightweight)
                # Register filters for path as well (e.g. TableName|to_kebab_case)
                path_env = Environment()
                from app.services.generator_service import to_kebab_case, to_camel_case, to_pascal_case
                path_env.filters['to_kebab_case'] = to_kebab_case
                path_env.filters['to_camel_case'] = to_camel_case
                path_env.filters['to_pascal_case'] = to_pascal_case
                
                # Render relative path
                try:
                    path_tmpl = path_env.from_string(tmpl.relative_path or "")
                    rendered_relative_path = path_tmpl.render(context)
                except:
                    rendered_relative_path = tmpl.relative_path
                
                # Root path is usually static but let's allow rendering too if needed, or just prepend
                root = tmpl.root_path or ""
                if root and not root.endswith("/"):
                    root += "/"
                
                full_path = root + rendered_relative_path

                # Write to file
                import os
                try:
                    # Create directories if not exist
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    # Write content
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(code)
                except Exception as e:
                    # Just log error but continue? Or fail? 
                    # For now, let's append error to code output or similar
                    print(f"Failed to write file {full_path}: {e}")
                    # code += f"\n\n// Error writing to file: {e}"

                table_files.append({
                    "template_name": tmpl.display_name or tmpl.name,
                    "path": full_path,
                    "root_path": tmpl.root_path,
                    "relative_path": rendered_relative_path,
                    "code": code
                })
            
            results.append({"table": table, "files": table_files})
            
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Data Source API (Database)
@app.post("/api/datasources/database", response_model=DatabaseConfigResponse)
async def create_database_config(ds: DatabaseConfigCreate, db: Session = Depends(get_db)):
    db_ds = DatabaseConfig(
        name=ds.name, 
        type=ds.type, 
        host=ds.host,
        port=ds.port,
        username=ds.username,
        password=ds.password,
        database_name=ds.database_name
    )
    db.add(db_ds)
    db.commit()
    db.refresh(db_ds)
    return db_ds

@app.get("/api/datasources/database", response_model=List[DatabaseConfigResponse])
async def get_database_configs(db: Session = Depends(get_db)):
    return db.query(DatabaseConfig).all()

@app.put("/api/datasources/database/{id}", response_model=DatabaseConfigResponse)
async def update_database_config(id: int, ds: DatabaseConfigCreate, db: Session = Depends(get_db)):
    db_ds = db.query(DatabaseConfig).filter(DatabaseConfig.id == id).first()
    if not db_ds:
        raise HTTPException(status_code=404, detail="DatabaseConfig not found")
    
    db_ds.name = ds.name
    db_ds.type = ds.type
    db_ds.host = ds.host
    db_ds.port = ds.port
    db_ds.username = ds.username
    db_ds.password = ds.password
    db_ds.database_name = ds.database_name
    
    db.commit()
    db.refresh(db_ds)
    return db_ds

@app.delete("/api/datasources/database/{id}")
async def delete_database_config(id: int, db: Session = Depends(get_db)):
    db_ds = db.query(DatabaseConfig).filter(DatabaseConfig.id == id).first()
    if not db_ds:
        raise HTTPException(status_code=404, detail="DatabaseConfig not found")
    db.delete(db_ds)
    db.commit()
    return {"ok": True}

# Redis API
@app.post("/api/datasources/redis", response_model=RedisConfigResponse)
async def create_redis_config(config: RedisConfigCreate, db: Session = Depends(get_db)):
    db_conf = RedisConfig(**config.dict())
    db.add(db_conf)
    db.commit()
    db.refresh(db_conf)
    return db_conf

@app.get("/api/datasources/redis", response_model=List[RedisConfigResponse])
async def get_redis_configs(db: Session = Depends(get_db)):
    return db.query(RedisConfig).all()

@app.put("/api/datasources/redis/{id}", response_model=RedisConfigResponse)
async def update_redis_config(id: int, config: RedisConfigCreate, db: Session = Depends(get_db)):
    db_conf = db.query(RedisConfig).filter(RedisConfig.id == id).first()
    if not db_conf:
        raise HTTPException(status_code=404, detail="RedisConfig not found")
    
    for key, value in config.dict().items():
        setattr(db_conf, key, value)
    
    db.commit()
    db.refresh(db_conf)
    return db_conf

@app.delete("/api/datasources/redis/{id}")
async def delete_redis_config(id: int, db: Session = Depends(get_db)):
    db_conf = db.query(RedisConfig).filter(RedisConfig.id == id).first()
    if not db_conf:
        raise HTTPException(status_code=404, detail="RedisConfig not found")
    db.delete(db_conf)
    db.commit()
    return {"ok": True}

# Elasticsearch API
@app.post("/api/datasources/es", response_model=ESConfigResponse)
async def create_es_config(config: ESConfigCreate, db: Session = Depends(get_db)):
    db_conf = ESConfig(**config.dict())
    db.add(db_conf)
    db.commit()
    db.refresh(db_conf)
    return db_conf

@app.get("/api/datasources/es", response_model=List[ESConfigResponse])
async def get_es_configs(db: Session = Depends(get_db)):
    return db.query(ESConfig).all()

@app.put("/api/datasources/es/{id}", response_model=ESConfigResponse)
async def update_es_config(id: int, config: ESConfigCreate, db: Session = Depends(get_db)):
    db_conf = db.query(ESConfig).filter(ESConfig.id == id).first()
    if not db_conf:
        raise HTTPException(status_code=404, detail="ESConfig not found")
    
    for key, value in config.dict().items():
        setattr(db_conf, key, value)
    
    db.commit()
    db.refresh(db_conf)
    return db_conf

@app.delete("/api/datasources/es/{id}")
async def delete_es_config(id: int, db: Session = Depends(get_db)):
    db_conf = db.query(ESConfig).filter(ESConfig.id == id).first()
    if not db_conf:
        raise HTTPException(status_code=404, detail="ESConfig not found")
    db.delete(db_conf)
    db.commit()
    return {"ok": True}

# LLM Config API
@app.post("/api/llm", response_model=LLMConfigResponse)
async def create_llm_config(config: LLMConfigCreate, db: Session = Depends(get_db)):
    # If this is marked active, deactivate others
    if config.is_active:
        db.query(LLMConfig).update({LLMConfig.is_active: 0})
    
    db_config = LLMConfig(
        name=config.name,
        provider=config.provider,
        base_url=config.base_url,
        api_key=config.api_key,
        model_name=config.model_name,
        is_active=1 if config.is_active else 0
    )
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config

@app.get("/api/llm", response_model=List[LLMConfigResponse])
async def get_llm_configs(db: Session = Depends(get_db)):
    return db.query(LLMConfig).all()

@app.put("/api/llm/{id}", response_model=LLMConfigResponse)
async def update_llm_config(id: int, config: LLMConfigCreate, db: Session = Depends(get_db)):
    db_config = db.query(LLMConfig).filter(LLMConfig.id == id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="LLM Config not found")
    
    # If this is marked active, deactivate others
    if config.is_active:
        db.query(LLMConfig).filter(LLMConfig.id != id).update({LLMConfig.is_active: 0})
    
    db_config.name = config.name
    db_config.provider = config.provider
    db_config.base_url = config.base_url
    db_config.api_key = config.api_key
    db_config.model_name = config.model_name
    db_config.is_active = 1 if config.is_active else 0
    
    db.commit()
    db.refresh(db_config)
    return db_config

@app.delete("/api/llm/{id}")
async def delete_llm_config(id: int, db: Session = Depends(get_db)):
    db_config = db.query(LLMConfig).filter(LLMConfig.id == id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="LLM Config not found")
    db.delete(db_config)
    db.commit()
    return {"ok": True}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
