package com.ripple.demo.repository;

import com.ripple.demo.entity.CodeNode;
import org.springframework.data.neo4j.repository.Neo4jRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface CodeRepository extends Neo4jRepository<CodeNode, String> {

}