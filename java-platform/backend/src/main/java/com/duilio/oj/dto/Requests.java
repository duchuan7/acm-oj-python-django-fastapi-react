package com.duilio.oj.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.*;

import java.time.Instant;
import java.util.*;

public final class Requests {
    private Requests() {}

    public record Login(
            @NotBlank @Size(max = 150) String username,
            @NotBlank @Size(max = 128) String password) {}

    public record Email(
            @NotBlank @jakarta.validation.constraints.Email @Size(max = 254) String email) {}

    public record Register(
            @NotBlank @Pattern(regexp = "[A-Za-z0-9_]{3,32}") String username,
            @NotBlank @jakarta.validation.constraints.Email @Size(max = 254) String email,
            @NotBlank @Size(min = 8, max = 128) String password,
            @Pattern(regexp = "[0-9]{6}") @NotNull String code,
            @Size(max = 128) String school,
            @Size(max = 64) String realName) {}

    public record PasswordReset(
            @NotBlank @jakarta.validation.constraints.Email String email,
            @NotBlank String code,
            @NotBlank @Size(min = 8, max = 128) String password) {}

    public record CaseDraft(
            @NotNull @Min(1) Integer order,
            @NotNull @Size(max = 1048576) String input,
            @NotNull @Size(max = 1048576) String output,
            @NotNull @Min(0) @Max(100) Integer score,
            boolean isSample) {}

    public record ProblemDraft(
            @NotBlank @Size(max = 200) String title,
            @NotBlank @Pattern(regexp = "[a-zA-Z0-9_-]{1,220}") String slug,
            @NotBlank @Size(max = 100000) String description,
            @NotNull @Size(max = 100000) String inputDescription,
            @NotNull @Size(max = 100000) String outputDescription,
            @NotNull @Size(max = 20) List<Map<String, String>> samples,
            @Min(100) @Max(10000) int timeLimitMs,
            @Min(32) @Max(1024) int memoryLimitMb,
            @Min(0) @Max(10000) Integer difficulty,
            @NotNull @Size(max = 30) List<@Size(max = 64) String> tags,
            @NotNull @Size(max = 200) String source,
            boolean isPublic,
            @NotNull @Size(max = 100) List<@Valid CaseDraft> testCases) {}

    public record Submit(
            @NotNull Long problem,
            Long contest,
            @NotBlank @Pattern(regexp = "C|CPP|JAVA|PYTHON") String language,
            @NotBlank @Size(max = 65536) String code) {}

    public record Review(@Size(max = 10000) String reviewMessage) {}

    public record Proposal(
            @NotNull @Valid ProblemDraft problem,
            @Pattern(regexp = "C|CPP|JAVA|PYTHON") @NotNull String standardLanguage,
            @NotBlank @Size(max = 65536) String standardCode) {}

    public record Editorial(
            @NotNull Long problem,
            @NotBlank @Size(max = 200) String title,
            @NotBlank @Size(max = 200000) String content) {}

    public record Blog(
            @NotBlank @Size(max = 200) String title,
            @NotBlank @Size(max = 200000) String content,
            @NotNull @Pattern(regexp = "DRAFT|PUBLISHED") String status) {}

    public record ContestProblemDraft(
            Long problem,
            @Valid ProblemDraft newProblem,
            @NotBlank @Pattern(regexp = "[A-Z0-9]{1,8}") String alias,
            @Min(1) @Max(100) int score,
            @Min(1) int order) {}

    public record ContestDraft(
            @NotBlank @Size(max = 200) String title,
            @NotNull @Size(max = 100000) String description,
            @NotNull @Pattern(regexp = "ACM|IOI") String rule,
            @NotNull Instant startAt,
            @NotNull Instant endAt,
            boolean isPublic,
            @Min(0) @Max(10080) int freezeRankMinutes,
            @NotNull @Size(max = 500) List<Long> participants,
            @NotNull @Size(max = 26) List<@Valid ContestProblemDraft> contestProblems) {}

    public record UserUpdate(
            @Pattern(regexp = "ADMIN|COACH|MEMBER") String role,
            Boolean active,
            @Size(max = 128) String school,
            @Size(max = 64) String realName) {}
}
