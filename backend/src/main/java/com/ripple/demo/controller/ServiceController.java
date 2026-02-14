package com.ripple.demo.controller;

import com.ripple.demo.dto.ParserOutputDTO;
import com.ripple.demo.service.GraphIngestService;
import org.springframework.web.bind.annotation.*;


@RestController
@RequestMapping("/api/graph")
@CrossOrigin(origins = "*")
public class ServiceController {

    private final GraphIngestService graphIngestService;

    public ServiceController(GraphIngestService graphIngestService) {
        this.graphIngestService = graphIngestService;
    }

    @GetMapping("/{projectId}")
    public ParserOutputDTO getGraph(@PathVariable String projectId) {
        return graphIngestService.fetchGraph();
    }
}
