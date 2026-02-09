package com.ripple.demo.controller;

import com.ripple.demo.entity.ServiceNode;
import com.ripple.demo.repository.ServiceRepository;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/services")
@CrossOrigin(origins = "*") // allows any data access from any origin, change to specific frontend domain later

public class ServiceController
{
    private final ServiceRepository serviceRepository;

    public ServiceController(ServiceRepository serviceRepository)
    {
        this.serviceRepository = serviceRepository;
    }

    @GetMapping
    public List<ServiceNode> findAll()
    {
        return serviceRepository.findAll();
    }

    @PostMapping
    public ServiceNode save(@RequestBody ServiceNode service)
    {
        return serviceRepository.save(service);
    }
}
