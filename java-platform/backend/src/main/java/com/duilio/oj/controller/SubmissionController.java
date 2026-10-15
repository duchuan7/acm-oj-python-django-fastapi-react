package com.duilio.oj.controller;

import com.duilio.oj.dto.Requests.Submit;
import com.duilio.oj.security.CurrentUser;
import com.duilio.oj.service.SubmissionService;

import jakarta.validation.Valid;

import org.springframework.context.annotation.Profile;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/submissions")
@Profile("!judge")
public class SubmissionController {
    private final SubmissionService submissions;
    private final CurrentUser current;

    public SubmissionController(SubmissionService submissions, CurrentUser current) {
        this.submissions = submissions;
        this.current = current;
    }

    @PostMapping
    Object create(@Valid @RequestBody Submit input) {
        return submissions.submit(input, current.required());
    }

    @GetMapping
    Object list(
            @RequestParam(required = false) Long problem,
            @RequestParam(required = false) Long contest,
            @RequestParam(required = false) String language,
            @RequestParam(required = false) String status,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(required = false) Long author) {
        return submissions.list(
                current.required(), problem, contest, language, status, page, author);
    }

    @GetMapping("/{id}")
    Object detail(@PathVariable Long id) {
        return submissions.detail(id, current.required());
    }
}
