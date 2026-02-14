package com.ripple.demo.controller;

import com.ripple.demo.entity.CodeNode;
import com.ripple.demo.repository.CodeRepository;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/graph")
@CrossOrigin(origins = "*") // allows any data access from any origin, change to specific frontend domain later

public class ServiceController
{
    private final CodeRepository codeRepository;

    public ServiceController(CodeRepository codeRepository)
    {
        this.codeRepository = codeRepository;
    }

    @GetMapping
    public List<CodeNode> getGraph()
    {
        return codeRepository.findAll();
    }

}
