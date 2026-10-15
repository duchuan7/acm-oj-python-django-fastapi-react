package com.duilio.oj.common;

import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestControllerAdvice
public class Errors {
    @ExceptionHandler(ApiException.class)
    ResponseEntity<?> business(ApiException e) {
        return ResponseEntity.status(e.status).body(Map.of("detail", e.getMessage()));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    ResponseEntity<?> validation(MethodArgumentNotValidException e) {
        String detail =
                e.getBindingResult().getFieldErrors().stream()
                        .map(f -> f.getField() + ": " + f.getDefaultMessage())
                        .findFirst()
                        .orElse("Invalid request");
        return ResponseEntity.badRequest().body(Map.of("detail", detail));
    }

    @ExceptionHandler({
        IllegalArgumentException.class,
        org.springframework.http.converter.HttpMessageNotReadableException.class
    })
    ResponseEntity<?> invalid(Exception e) {
        return ResponseEntity.badRequest().body(Map.of("detail", "Invalid request data"));
    }

    @ExceptionHandler(DataIntegrityViolationException.class)
    ResponseEntity<?> conflict(Exception e) {
        return ResponseEntity.status(409)
                .body(Map.of("detail", "Duplicate value or referenced record"));
    }

    @ExceptionHandler(org.springframework.data.redis.RedisConnectionFailureException.class)
    ResponseEntity<?> unavailable(Exception e) {
        return ResponseEntity.status(503).body(Map.of("detail", "Redis temporarily unavailable"));
    }
}
