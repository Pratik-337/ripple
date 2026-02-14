package com.ripple.demo.repository;

import com.ripple.demo.entity.CodeNode;
import com.ripple.demo.entity.CodeNode;
import org.springframework.data.neo4j.repository.Neo4jRepository;


public interface CodeRepository extends Neo4jRepository<CodeNode, Long>
{
    CodeNode findByName(String name);
}
