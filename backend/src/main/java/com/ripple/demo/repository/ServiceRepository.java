package com.ripple.demo.repository;

import com.ripple.demo.entity.ServiceNode;
import org.springframework.data.neo4j.repository.Neo4jRepository;
import java.util.List;


public interface ServiceRepository extends Neo4jRepository<ServiceNode, Long>
{
    ServiceNode findByName(String name);
}
