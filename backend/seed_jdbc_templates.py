from app.models import SessionLocal, TemplateGroup, Template
from datetime import datetime

def seed_jdbc_templates():
    db = SessionLocal()
    try:
        # 1. Create Group
        group_name = "Spring Boot JdbcTemplate"
        group = db.query(TemplateGroup).filter(TemplateGroup.name == group_name).first()
        if not group:
            group = TemplateGroup(
                name=group_name,
                description="Spring Boot stack using NamedParameterJdbcTemplate, Lombok, and manual SQL mapping."
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
                "prompt": "Generate a Java entity class using Lombok. Use 'TableName' as class name. Map DB types to Java types.",
                "content": """package com.example.domain.entity;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;

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
public class {{ TableName }} implements Serializable {

    private static final long serialVersionUID = 1L;

    {% for col in columns %}
    {% if col.comment %}
    /**
     * {{ col.comment }}
     */
    {% endif %}
    private {{ col.type|to_java_type }} {{ col.name|to_camel_case }};

    {% endfor %}
}"""
            },
            {
                "name": "dao.java.jinja2",
                "display_name": "DAO (JdbcTemplate)",
                "root_path": "src/main/java",
                "relative_path": "com/example/dao/{{ TableName }}Dao.java",
                "prompt": "Generate a DAO class using NamedParameterJdbcTemplate for CRUD operations.",
                "content": """package com.example.dao;

import com.example.domain.entity.{{ TableName }};
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.namedparam.BeanPropertySqlParameterSource;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.jdbc.support.GeneratedKeyHolder;
import org.springframework.jdbc.support.KeyHolder;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
@RequiredArgsConstructor
public class {{ TableName }}Dao {

    private final NamedParameterJdbcTemplate jdbcTemplate;

    public Long save({{ TableName }} entity) {
        String sql = "INSERT INTO {{ name }} ({% for col in columns if not col.primary_key %}{{ col.name }}{% if not loop.last %}, {% endif %}{% endfor %}) " +
                     "VALUES ({% for col in columns if not col.primary_key %}:{{ col.name|to_camel_case }}{% if not loop.last %}, {% endif %}{% endfor %})";
        
        KeyHolder keyHolder = new GeneratedKeyHolder();
        jdbcTemplate.update(sql, new BeanPropertySqlParameterSource(entity), keyHolder);
        
        Number key = keyHolder.getKey();
        if (key != null) {
            entity.setId(key.longValue());
            return key.longValue();
        }
        return null;
    }

    public int update({{ TableName }} entity) {
        String sql = "UPDATE {{ name }} SET {% for col in columns if not col.primary_key %}{{ col.name }} = :{{ col.name|to_camel_case }}{% if not loop.last %}, {% endif %}{% endfor %} " +
                     "WHERE id = :id";
        return jdbcTemplate.update(sql, new BeanPropertySqlParameterSource(entity));
    }

    public int deleteById(Long id) {
        String sql = "DELETE FROM {{ name }} WHERE id = :id";
        return jdbcTemplate.update(sql, new MapSqlParameterSource("id", id));
    }

    public Optional<{{ TableName }}> findById(Long id) {
        String sql = "SELECT * FROM {{ name }} WHERE id = :id";
        try {
            return Optional.ofNullable(jdbcTemplate.queryForObject(sql, new MapSqlParameterSource("id", id), (rs, rowNum) -> {
                return {{ TableName }}.builder()
                    {% for col in columns %}
                    .{{ col.name|to_camel_case }}(rs.getObject("{{ col.name }}", {{ col.type|to_java_type }}.class))
                    {% endfor %}
                    .build();
            }));
        } catch (Exception e) {
            return Optional.empty();
        }
    }

    public List<{{ TableName }}> findAll() {
        String sql = "SELECT * FROM {{ name }}";
        return jdbcTemplate.query(sql, (rs, rowNum) -> {
            return {{ TableName }}.builder()
                {% for col in columns %}
                .{{ col.name|to_camel_case }}(rs.getObject("{{ col.name }}", {{ col.type|to_java_type }}.class))
                {% endfor %}
                .build();
        });
    }
}"""
            },
            {
                "name": "service.java.jinja2",
                "display_name": "Service",
                "root_path": "src/main/java",
                "relative_path": "com/example/service/{{ TableName }}Service.java",
                "prompt": "Generate a Service class that uses the DAO.",
                "content": """package com.example.service;

import com.example.dao.{{ TableName }}Dao;
import com.example.domain.entity.{{ TableName }};
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class {{ TableName }}Service {

    private final {{ TableName }}Dao dao;

    @Transactional
    public Long create({{ TableName }} entity) {
        return dao.save(entity);
    }

    @Transactional
    public void update({{ TableName }} entity) {
        dao.update(entity);
    }

    @Transactional
    public void delete(Long id) {
        dao.deleteById(id);
    }

    public Optional<{{ TableName }}> getById(Long id) {
        return dao.findById(id);
    }

    public List<{{ TableName }}> list() {
        return dao.findAll();
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
    public R<Long> save(@RequestBody {{ TableName }} entity) {
        return R.ok(service.create(entity));
    }

    @PutMapping("/{id}")
    public R<Void> update(@PathVariable Long id, @RequestBody {{ TableName }} entity) {
        entity.setId(id);
        service.update(entity);
        return R.ok();
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
        print("Done seeding JdbcTemplate templates.")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_jdbc_templates()
