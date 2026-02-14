package com.ripple.demo.service;

import com.ripple.demo.dto.ParserOutputDTO;
import org.springframework.stereotype.Service;
import org.springframework.data.neo4j.core.Neo4jClient;
import java.util.Map;

@Service
public class GraphIngestService {

    private final Neo4jClient neo4jClient;

    public GraphIngestService(Neo4jClient neo4jClient) {
        this.neo4jClient = neo4jClient;
    }

    public void saveGraph(ParserOutputDTO graphData) {
        String nodeQuery = """
            UNWIND $nodes AS n
            MERGE (e:CodeEntity {id: n.id})
            SET e.type = n.type, 
                e.language = n.language
        """;

        neo4jClient.query(nodeQuery)
                .bind(graphData.getNodes()).to("nodes")
                .run();

        String relQuery = """
            UNWIND $rels AS r
            MATCH (source:CodeEntity {id: r.from})
            MATCH (target:CodeEntity {id: r.to})
            MERGE (source)-[rel:DEPENDS_ON]->(target)
            SET rel.type = r.type
        """;

        neo4jClient.query(relQuery)
                .bind(graphData.getRelations()).to("rels")
                .run();
    }
}
