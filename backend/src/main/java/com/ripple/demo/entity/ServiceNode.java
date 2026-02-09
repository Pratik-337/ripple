package com.ripple.demo.entity;

import org.springframework.data.neo4j.core.schema.Id;
import org.springframework.data.neo4j.core.schema.Node;
import org.springframework.data.neo4j.core.schema.Relationship;
import org.springframework.data.neo4j.core.schema.GeneratedValue;
import lombok.Data;
import java.util.List;
import java.util.ArrayList;

@Node("Service")
@Data
public class ServiceNode {
    @Id @GeneratedValue
    private Long id;

    private String name;
    private String owner;
    private String criticality;

    @Relationship(type = "DEPENDS_ON", direction = Relationship.Direction.OUTGOING)
    private List<ServiceNode> dependencies = new ArrayList<>();
}