package com.ripple.demo.dto;

import lombok.Data;
import java.util.List;


@Data

public class ParserOutputDTO {
    private List<NodeDTO> nodes;
    private List<RelationDTO> relations;

    @Data
    public static class NodeDTO {
        private String id;
        private String type;
        private String language;
    }

    @Data
    public static class RelationDTO {
        private String from;
        private String to;
        private String type;
    }
}
