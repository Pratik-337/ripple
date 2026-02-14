package com.ripple.demo.service;

import com.ripple.demo.dto.ParserOutputDTO;
import org.springframework.data.neo4j.core.Neo4jClient;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
public class GraphIngestService {

    private final Neo4jClient neo4jClient;

    public GraphIngestService(Neo4jClient neo4jClient) {
        this.neo4jClient = neo4jClient;
    }

    public void saveGraph(ParserOutputDTO graphData) {
        // 1. Convert NodeDTOs to Maps
        List<Map<String, Object>> nodeMaps = graphData.getNodes().stream()
                .map(n -> {
                    Map<String, Object> map = new HashMap<>();
                    map.put("id", n.getId());
                    map.put("type", n.getType());
                    map.put("language", n.getLanguage());
                    return map;
                })
                .collect(Collectors.toList());

        String nodeQuery = """
            UNWIND $nodes AS n
            MERGE (e:CodeNode {id: n.id})
            SET e.type = n.type, 
                e.language = n.language
        """;

        neo4jClient.query(nodeQuery)
                .bind(nodeMaps).to("nodes") // Now passing Maps, not Objects!
                .run();

        // 2. Convert RelationDTOs to Maps
        List<Map<String, Object>> relMaps = graphData.getRelations().stream()
                .map(r -> {
                    Map<String, Object> map = new HashMap<>();
                    map.put("from", r.getFrom());
                    map.put("to", r.getTo());
                    map.put("type", r.getType());
                    return map;
                })
                .collect(Collectors.toList());

        String relQuery = """
            UNWIND $rels AS r
            MATCH (source:CodeNode {id: r.from})
            MATCH (target:CodeNode {id: r.to})
            MERGE (source)-[rel:DEPENDS_ON]->(target)
            SET rel.type = r.type
        """;

        neo4jClient.query(relQuery)
                .bind(relMaps).to("rels") // Now passing Maps!
                .run();
    }
}