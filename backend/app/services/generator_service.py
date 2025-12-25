import json
import re
from jinja2 import Environment, DictLoader
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models import Template
from app.services.llm_service import llm_service

# Custom Filters
def to_camel_case(s: str) -> str:
    """user_name -> userName"""
    if not s: return ""
    parts = s.split('_')
    return parts[0] + ''.join(x.title() for x in parts[1:])

def to_pascal_case(s: str) -> str:
    """user_name -> UserName"""
    if not s: return ""
    return ''.join(x.title() for x in s.replace('-', '_').split('_'))

def to_kebab_case(s: str) -> str:
    """UserTable -> user-table"""
    if not s: return ""
    # Handle PascalCase/CamelCase to kebab-case
    s = re.sub(r'(?<!^)(?=[A-Z])', '-', s).lower()
    return s.replace('_', '-')

def to_java_type(sql_type: str) -> str:
    """VARCHAR -> String"""
    if not sql_type: return "String"
    sql_type = sql_type.upper()
    
    if 'BIGINT' in sql_type:
        return 'Long'
    if 'INT' in sql_type or 'INTEGER' in sql_type:
        return 'Integer'
    if 'CHAR' in sql_type or 'TEXT' in sql_type or 'STRING' in sql_type:
        return 'String'
    if 'DATETIME' in sql_type or 'TIMESTAMP' in sql_type:
        return 'LocalDateTime'
    if 'DATE' in sql_type:
        return 'LocalDate'
    if 'TIME' in sql_type:
        return 'LocalTime'
    if 'DECIMAL' in sql_type or 'NUMERIC' in sql_type:
        return 'BigDecimal'
    if 'DOUBLE' in sql_type:
        return 'Double'
    if 'FLOAT' in sql_type:
        return 'Float'
    if 'BOOL' in sql_type or 'BIT' in sql_type:
        return 'Boolean'
    if 'BLOB' in sql_type or 'BINARY' in sql_type:
        return 'byte[]'
        
    return 'String' # Default

def format_schema_to_prompt(schema: Dict[str, Any]) -> str:
    """Formats table schema into a readable string for LLM."""
    table_name = schema.get("name", "Unknown")
    comment = schema.get("comment", "")
    columns = schema.get("columns", [])
    
    lines = []
    lines.append(f"Table Name: {table_name}")
    if comment:
        lines.append(f"Table Comment: {comment}")
    lines.append("Columns:")
    
    for col in columns:
        c_name = col['name']
        c_type = col['type']
        c_pk = " (PK)" if col.get('primary_key') else ""
        c_comment = f" - {col['comment']}" if col.get('comment') else ""
        lines.append(f"- {c_name} ({c_type}){c_pk}{c_comment}")
        
    return "\n".join(lines)

class GeneratorService:
    def __init__(self):
        # We will use DictLoader which allows loading templates from a dictionary
        # However, since templates are in DB, we'll need to fetch them dynamically or recreate env
        # For simplicity, we can recreate env or use a custom loader if needed.
        # But simpler approach for render: just create a temporary env with the specific template content
        pass

    def get_available_templates(self, db: Session) -> list[str]:
        """Returns a list of available template names from DB."""
        templates = db.query(Template.name).all()
        return [t[0] for t in templates]

    def get_template(self, db: Session, template_name: str) -> Template:
        """Returns the template object."""
        template = db.query(Template).filter(Template.name == template_name).first()
        if not template:
            raise Exception(f"Template {template_name} not found")
        return template

    def get_template_content(self, db: Session, template_id: int) -> Dict[str, Any]:
        """Returns the content and metadata of a template."""
        template = db.query(Template).filter(Template.id == template_id).first()
        if not template:
            raise Exception(f"Template not found")
        return {
            "id": template.id,
            "group_id": template.group_id,
            "content": template.content,
            "root_path": template.root_path,
            "relative_path": template.relative_path,
            "display_name": template.display_name,
            "prompt": template.prompt,
            "name": template.name
        }

    def save_template(self, db: Session, group_id: int, template_name: str, content: str, root_path: str = "", relative_path: str = "", display_name: str = "", prompt: str = ""):
        """Saves a new template to DB."""
        # For simplicity in this refactor, we always create new or update by ID in the controller.
        # This function is now mostly a wrapper for creating.
        template = Template(
            group_id=group_id,
            name=template_name, 
            content=content, 
            root_path=root_path,
            relative_path=relative_path,
            display_name=display_name,
            prompt=prompt
        )
        db.add(template)
        db.commit()

    def delete_template(self, db: Session, template_id: int):
        """Deletes a template from DB."""
        template = db.query(Template).filter(Template.id == template_id).first()
        if not template:
            raise Exception(f"Template not found")
        db.delete(template)
        db.commit()

    def generate_code(self, db: Session, template_id: int, context: Dict[str, Any], use_llm: bool = False) -> str:
        """Generates code based on a template and context."""
        template = db.query(Template).filter(Template.id == template_id).first()
        if not template:
            raise Exception(f"Template not found")
        
        # Branch 1: LLM Generation
        if use_llm:
             # Check if prompt exists
             if not template.prompt:
                 raise Exception("Template has no prompt configured for AI generation.")
             
             # Prepare Prompt
             # We inject schema_text into context
             schema_text = format_schema_to_prompt(context)
             llm_context = context.copy()
             llm_context["schema_text"] = schema_text
             
             # Render Prompt Template (The prompt itself can use Jinja2)
             env = Environment(loader=DictLoader({"prompt": template.prompt}))
             try:
                 tmpl = env.get_template("prompt")
                 rendered_prompt = tmpl.render(llm_context)
             except Exception as e:
                 raise Exception(f"Error rendering prompt template: {str(e)}")
             
             # Call LLM
             return llm_service.chat_completion(db, rendered_prompt)

        # Branch 2: Standard Jinja2 Generation
        env = Environment(loader=DictLoader({str(template.id): template.content}))
        
        # Register Filters
        env.filters['to_camel_case'] = to_camel_case
        env.filters['to_pascal_case'] = to_pascal_case
        env.filters['to_kebab_case'] = to_kebab_case
        env.filters['to_java_type'] = to_java_type
        
        try:
            tmpl = env.get_template(str(template.id))
            return tmpl.render(context)
        except Exception as e:
            raise Exception(f"Error generating code from template {template.name}: {str(e)}")

generator_service = GeneratorService()
