from app.models import SessionLocal, TemplateGroup, Template
from datetime import datetime

def seed_templates():
    db = SessionLocal()
    try:
        # 1. Create Group
        group_name = "Spring Boot Mybatis-Plus"
        group = db.query(TemplateGroup).filter(TemplateGroup.name == group_name).first()
        if not group:
            group = TemplateGroup(
                name=group_name,
                description="Standard Spring Boot stack with Mybatis-Plus, MapStruct, and Lombok."
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
                "name": "domain.java.jinja2",
                "display_name": "Domain Entity",
                "root_path": "src/main/java",
                "relative_path": "com/example/domain/entity/{{ TableName }}.java",
                "prompt": "Generate a Java entity class for table '{{ TableName }}'.\nTable Schema:\n{{ schema_text }}\n\nRequirements:\n- Use Lombok @Data, @Accessors(chain=true)\n- Use Mybatis-Plus @TableName, @TableId\n- Use Swagger @Schema\n- Implement Serializable",
                "content": """package com.example.domain.entity;

import com.baomidou.mybatisplus.annotation.*;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;

import java.io.Serializable;
import java.time.LocalDateTime;
import java.math.BigDecimal;

/**
 * {{ comment or TableName }}
 */
@Data
@EqualsAndHashCode(callSuper = false)
@Accessors(chain = true)
@TableName("{{ name }}")
@Schema(description = "{{ comment or TableName }}")
public class {{ TableName }} implements Serializable {

    private static final long serialVersionUID = 1L;

    {% for col in columns %}
    {% if col.comment %}
    /**
     * {{ col.comment }}
     */
    @Schema(description = "{{ col.comment }}")
    {% endif %}
    {% if col.primary_key %}
    @TableId(value = "{{ col.name }}", type = IdType.AUTO)
    {% else %}
    @TableField("{{ col.name }}")
    {% endif %}
    private {{ col.type|to_java_type }} {{ col.name|to_camel_case }};

    {% endfor %}
}"""
            },
            {
                "name": "mapper.java.jinja2",
                "display_name": "Mapper Interface",
                "root_path": "src/main/java",
                "relative_path": "com/example/mapper/{{ TableName }}Mapper.java",
                "prompt": "Generate a Mybatis-Plus Mapper interface for '{{ TableName }}'.\nTable Schema:\n{{ schema_text }}\n\nRequirements:\n- Extend BaseMapper\n- Use @Mapper annotation",
                "content": """package com.example.mapper;

import com.example.domain.entity.{{ TableName }};
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;

/**
 * {{ comment or TableName }} Mapper
 */
@Mapper
public interface {{ TableName }}Mapper extends BaseMapper<{{ TableName }}> {

}"""
            },
            {
                "name": "service.java.jinja2",
                "display_name": "Service Interface",
                "root_path": "src/main/java",
                "relative_path": "com/example/service/{{ TableName }}Service.java",
                "prompt": "Generate a Service interface for '{{ TableName }}'.\nTable Schema:\n{{ schema_text }}\n\nRequirements:\n- Extend IService<{{ TableName }}>",
                "content": """package com.example.service;

import com.example.domain.entity.{{ TableName }};
import com.baomidou.mybatisplus.extension.service.IService;

/**
 * {{ comment or TableName }} Service
 */
public interface {{ TableName }}Service extends IService<{{ TableName }}> {

}"""
            },
            {
                "name": "service_impl.java.jinja2",
                "display_name": "Service Implementation",
                "root_path": "src/main/java",
                "relative_path": "com/example/service/impl/{{ TableName }}ServiceImpl.java",
                "prompt": "Generate a Service implementation for '{{ TableName }}'.\nTable Schema:\n{{ schema_text }}\n\nRequirements:\n- Extend ServiceImpl\n- Implement {{ TableName }}Service\n- Use @Service annotation",
                "content": """package com.example.service.impl;

import com.example.domain.entity.{{ TableName }};
import com.example.mapper.{{ TableName }}Mapper;
import com.example.service.{{ TableName }}Service;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import org.springframework.stereotype.Service;

/**
 * {{ comment or TableName }} Service Implementation
 */
@Service
public class {{ TableName }}ServiceImpl extends ServiceImpl<{{ TableName }}Mapper, {{ TableName }}> implements {{ TableName }}Service {

}"""
            },
            {
                "name": "vo.java.jinja2",
                "display_name": "View Object (VO)",
                "root_path": "src/main/java",
                "relative_path": "com/example/domain/vo/{{ TableName }}VO.java",
                "prompt": "Generate a VO class for frontend display. Similar to Entity but without DB annotations.",
                "content": """package com.example.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import java.time.LocalDateTime;
import java.math.BigDecimal;

/**
 * {{ comment or TableName }} VO
 */
@Data
@Schema(description = "{{ comment or TableName }}")
public class {{ TableName }}VO {

    {% for col in columns %}
    @Schema(description = "{{ col.comment or col.name }}")
    private {{ col.type|to_java_type }} {{ col.name|to_camel_case }};

    {% endfor %}
}"""
            },
            {
                "name": "param.java.jinja2",
                "display_name": "Request Param",
                "root_path": "src/main/java",
                "relative_path": "com/example/domain/param/{{ TableName }}Param.java",
                "prompt": "Generate a Param class for creating/updating.",
                "content": """package com.example.domain.param;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import java.time.LocalDateTime;
import java.math.BigDecimal;
import javax.validation.constraints.*;

/**
 * {{ comment or TableName }} Param
 */
@Data
@Schema(description = "{{ comment or TableName }} Request Param")
public class {{ TableName }}Param {

    {% for col in columns %}
    {% if not col.primary_key and col.name not in ['created_at', 'updated_at', 'create_time', 'update_time'] %}
    @Schema(description = "{{ col.comment or col.name }}")
    private {{ col.type|to_java_type }} {{ col.name|to_camel_case }};
    {% endif %}
    {% endfor %}
}"""
            },
            {
                "name": "converter.java.jinja2",
                "display_name": "MapStruct Converter",
                "root_path": "src/main/java",
                "relative_path": "com/example/convert/{{ TableName }}Converter.java",
                "prompt": "Generate a MapStruct converter interface.",
                "content": """package com.example.convert;

import com.example.domain.entity.{{ TableName }};
import com.example.domain.vo.{{ TableName }}VO;
import com.example.domain.param.{{ TableName }}Param;
import org.mapstruct.Mapper;
import org.mapstruct.factory.Mappers;
import java.util.List;

@Mapper
public interface {{ TableName }}Converter {
    {{ TableName }}Converter INSTANCE = Mappers.getMapper({{ TableName }}Converter.class);

    {{ TableName }}VO toVO({{ TableName }} entity);
    
    List<{{ TableName }}VO> toVOList(List<{{ TableName }}> list);

    {{ TableName }} toEntity({{ TableName }}Param param);
}"""
            },
            {
                "name": "controller.java.jinja2",
                "display_name": "Controller",
                "root_path": "src/main/java",
                "relative_path": "com/example/controller/{{ TableName }}Controller.java",
                "prompt": "Generate a Spring Boot Controller for '{{ TableName }}'.\nTable Schema:\n{{ schema_text }}\n\nRequirements:\n- RESTful API (GET/POST/PUT/DELETE)\n- Use @RestController, @RequestMapping\n- Use Swagger annotations\n- Use {{ TableName }}Service\n- Return R<T> wrapper",
                "content": """package com.example.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.domain.entity.{{ TableName }};
import com.example.domain.param.{{ TableName }}Param;
import com.example.domain.vo.{{ TableName }}VO;
import com.example.service.{{ TableName }}Service;
import com.example.convert.{{ TableName }}Converter;
import com.example.common.api.R;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.util.List;

/**
 * {{ comment or TableName }} Controller
 */
@Tag(name = "{{ comment or TableName }}")
@RestController
@RequestMapping("/{{ TableName|to_kebab_case }}")
public class {{ TableName }}Controller {

    @Autowired
    private {{ TableName }}Service service;

    @Operation(summary = "Get by ID")
    @GetMapping("/{id}")
    public R<{{ TableName }}VO> getById(@PathVariable Long id) {
        {{ TableName }} entity = service.getById(id);
        return R.ok({{ TableName }}Converter.INSTANCE.toVO(entity));
    }

    @Operation(summary = "Page Query")
    @GetMapping("/page")
    public R<IPage<{{ TableName }}VO>> page(@RequestParam(defaultValue = "1") Long current, 
                                            @RequestParam(defaultValue = "10") Long size) {
        IPage<{{ TableName }}> page = service.page(new Page<>(current, size));
        IPage<{{ TableName }}VO> voPage = page.convert({{ TableName }}Converter.INSTANCE::toVO);
        return R.ok(voPage);
    }

    @Operation(summary = "Create")
    @PostMapping
    public R<Boolean> save(@RequestBody @Valid {{ TableName }}Param param) {
        {{ TableName }} entity = {{ TableName }}Converter.INSTANCE.toEntity(param);
        return R.ok(service.save(entity));
    }

    @Operation(summary = "Update")
    @PutMapping("/{id}")
    public R<Boolean> update(@PathVariable Long id, @RequestBody @Valid {{ TableName }}Param param) {
        {{ TableName }} entity = {{ TableName }}Converter.INSTANCE.toEntity(param);
        entity.setId(id);
        return R.ok(service.updateById(entity));
    }

    @Operation(summary = "Delete")
    @DeleteMapping("/{id}")
    public R<Boolean> remove(@PathVariable Long id) {
        return R.ok(service.removeById(id));
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
        print("Done seeding templates.")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_templates()
