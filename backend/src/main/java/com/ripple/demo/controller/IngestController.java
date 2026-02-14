package com.ripple.demo.controller;

import com.ripple.demo.dto.ParserOutputDTO;
import com.ripple.demo.service.GraphIngestService;
import org.springframework.web.bind.annotation.*;


@RestController
@RequestMapping("/api/ingest")
@CrossOrigin(origins = "*")
public class IngestController {

    private final GraphIngestService ingestService;

    public IngestController(GraphIngestService ingestService) {
        this.ingestService = ingestService;
    }

    @PostMapping
    public String ingestGraph(@RequestBody ParserOutputDTO graphData) {
        ingestService.saveGraph(graphData);
        return "Graph Ingested: " + graphData.getNodes().size() + " nodes processed.";
    }
}
