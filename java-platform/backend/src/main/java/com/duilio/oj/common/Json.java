package com.duilio.oj.common;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;

import org.springframework.stereotype.Component;

import java.util.*;

@Component
public class Json {
    public final ObjectMapper mapper;

    public Json(ObjectMapper mapper) {
        this.mapper = mapper;
    }

    public String write(Object value) {
        try {
            return mapper.writeValueAsString(value);
        } catch (Exception e) {
            throw new IllegalArgumentException("Invalid JSON", e);
        }
    }

    public <T> T read(String value, Class<T> type) {
        try {
            return mapper.readValue(value, type);
        } catch (Exception e) {
            throw new IllegalArgumentException("Invalid JSON", e);
        }
    }

    public Map<String, Object> view(Object value) {
        return mapper.convertValue(value, new TypeReference<LinkedHashMap<String, Object>>() {});
    }
}
