package com.ripple.demo.entity;

import org.springframework.data.neo4j.core.schema.Id;
import org.springframework.data.neo4j.core.schema.Node;
import org.springframework.data.neo4j.core.schema.Property;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

@Node("CodeEntity")
@Data
@NoArgsConstructor
@AllArgsConstructor

public class CodeNode {

    @Id
    private String id;

    @Property("type")
    private String type;

    @Property("language")
    private String language;

    private String owner;
}
