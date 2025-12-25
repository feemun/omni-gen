from app.models import SessionLocal, TemplateGroup, Template
from datetime import datetime

def seed_spring_data_jdbc_templates():
    db = SessionLocal()
    try:
        # 1. Create Group
        group_name = "Spring Boot Data JDBC"
        group = db.query(TemplateGroup).filter(TemplateGroup.name == group_name).first()
        if not group:
            group = TemplateGroup(
                name=group_name,
                description="Spring Boot stack using Spring Data JDBC (lighter than JPA)."
            )
            db.add(group)
            db.commit()
            db.refresh(group)
            print(f"Created Group: {group.name}")
        else:
            print(f"Group exists: {group.name}")

        # 2. Define Templates
        templates = [
            {
                "name": "entity.java.jinja2",
                "display_name": "Entity",
                "root_path": "src/main/java",
                "relative_path": "com/example/domain/entity/{{ TableName }}.java",
                "prompt": "Generate a Spring Data JDBC entity. Use @Table, @Id, @Column.",
                "content": """package com.example.domain.entity;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;
import org.springframework.data.annotation.Id;
import org.springframework.data.relational.core.mapping.Column;
import org.springframework.data.relational.core.mapping.Table;

import java.io.Serializable;
import java.time.LocalDateTime;
import java.math.BigDecimal;

/**
 * {{ comment or TableName }}
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Table("{{ name }}")
public class {{ TableName }} implements Serializable {

    private static final long serialVersionUID = 1L;

    {% for col in columns %}
    {% if col.comment %}
    /**
     * {{ col.comment }}
     */
    {% endif %}
    {% if col.primary_key %}
    @Id
    {% endif %}
    @Column("{{ col.name }}")
    private {{ col.type|to_java_type }} {{ col.name|to_camel_case }};

    {% endfor %}
}"""
            },
            {
                "name": "repository.java.jinja2",
                "display_name": "Repository",
                "root_path": "src/main/java",
                "relative_path": "com/example/repository/{{ TableName }}Repository.java",
                "prompt": "Generate a Spring Data JDBC Repository extending CrudRepository.",
                "content": """package com.example.repository;

import com.example.domain.entity.{{ TableName }};
import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface {{ TableName }}Repository extends CrudRepository<{{ TableName }}, Long> {
    
    // Spring Data JDBC provides findAll(), save(), findById(), deleteById() etc.
    // Override findAll to return List instead of Iterable if preferred
    @Override
    List<{{ TableName }}> findAll();
}"""
            },
            {
                "name": "service.java.jinja2",
                "display_name": "Service",
                "root_path": "src/main/java",
                "relative_path": "com/example/service/{{ TableName }}Service.java",
                "prompt": "Generate a Service class that uses the Repository.",
                "content": """package com.example.service;

import com.example.domain.entity.{{ TableName }};
import com.example.repository.{{ TableName }}Repository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class {{ TableName }}Service {

    private final {{ TableName }}Repository repository;

    @Transactional
    public {{ TableName }} save({{ TableName }} entity) {
        return repository.save(entity);
    }

    @Transactional
    public void delete(Long id) {
        repository.deleteById(id);
    }

    public Optional<{{ TableName }}> getById(Long id) {
        return repository.findById(id);
    }

    public List<{{ TableName }}> list() {
        return repository.findAll();
    }
}"""
            },
            {
                "name": "controller.java.jinja2",
                "display_name": "Controller",
                "root_path": "src/main/java",
                "relative_path": "com/example/controller/{{ TableName }}Controller.java",
                "prompt": "Generate a Controller.",
                "content": """package com.example.controller;

import com.example.domain.entity.{{ TableName }};
import com.example.service.{{ TableName }}Service;
import com.example.common.api.R;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/{{ TableName|to_kebab_case }}")
@RequiredArgsConstructor
public class {{ TableName }}Controller {

    private final {{ TableName }}Service service;

    @GetMapping("/{id}")
    public R<{{ TableName }}> getById(@PathVariable Long id) {
        return R.ok(service.getById(id).orElse(null));
    }

    @GetMapping
    public R<List<{{ TableName }}>> list() {
        return R.ok(service.list());
    }

    @PostMapping
    public R<{{ TableName }}> save(@RequestBody {{ TableName }} entity) {
        return R.ok(service.save(entity));
    }

    @PutMapping("/{id}")
    public R<{{ TableName }}> update(@PathVariable Long id, @RequestBody {{ TableName }} entity) {
        // Ensure ID is set for update
        // Note: Spring Data JDBC distinguishes insert/update by whether ID is null (or new)
        // If your entity uses @Id, setting it will make SD-JDBC try an UPDATE.
        try {
            java.lang.reflect.Field idField = entity.getClass().getDeclaredField("id");
            idField.setAccessible(true);
            idField.set(entity, id);
        } catch (Exception e) {
            // ignore or handle specific ID field name logic
        }
        return R.ok(service.save(entity));
    }

    @DeleteMapping("/{id}")
    public R<Void> delete(@PathVariable Long id) {
        service.delete(id);
        return R.ok();
    }
}"""
            }
        ]

        # 3. Save Templates
        for tmpl_data in templates:
            # Check if exists
            exists = db.query(Template).filter(
                Template.group_id == group.id, 
                Template.name == tmpl_data["name"]
            ).first()
            
            if exists:
                # Update
                exists.content = tmpl_data["content"]
                exists.root_path = tmpl_data["root_path"]
                exists.relative_path = tmpl_data["relative_path"]
                exists.display_name = tmpl_data["display_name"]
                exists.prompt = tmpl_data["prompt"]
                print(f"Updated Template: {exists.name}")
            else:
                # Create
                t = Template(
                    group_id=group.id,
                    name=tmpl_data["name"],
                    content=tmpl_data["content"],
                    root_path=tmpl_data["root_path"],
                    relative_path=tmpl_data["relative_path"],
                    display_name=tmpl_data["display_name"],
                    prompt=tmpl_data["prompt"]
                )
                db.add(t)
                print(f"Created Template: {t.name}")
        
        db.commit()
        print("Done seeding Spring Data JDBC templates.")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_spring_data_jdbc_templates()
