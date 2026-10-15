package com.duilio.oj.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.duilio.oj.common.*;
import com.duilio.oj.dto.Requests.Submit;
import com.duilio.oj.mapper.*;
import com.duilio.oj.model.*;
import com.duilio.oj.security.CurrentUser;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.*;

@Service
public class SubmissionService {
    private final SubmissionMapper submissions;
    private final JudgeOutboxMapper outbox;
    private final CaseResultMapper results;
    private final TestCaseMapper cases;
    private final ProblemMapper problems;
    private final UserMapper users;
    private final ContestService contests;
    private final AbuseService abuse;
    private final Json json;

    public SubmissionService(
            SubmissionMapper submissions,
            JudgeOutboxMapper outbox,
            CaseResultMapper results,
            TestCaseMapper cases,
            ProblemMapper problems,
            UserMapper users,
            ContestService contests,
            AbuseService abuse,
            Json json) {
        this.submissions = submissions;
        this.outbox = outbox;
        this.results = results;
        this.cases = cases;
        this.problems = problems;
        this.users = users;
        this.contests = contests;
        this.abuse = abuse;
        this.json = json;
    }

    @Transactional
    public Object submit(Submit input, User actor) {
        int size = input.code().getBytes(StandardCharsets.UTF_8).length;
        ApiException.require(size <= 65536, 400, "Code must be <= 64 KiB");
        contests.validateSubmission(input.problem(), input.contest(), actor);
        ApiException.require(
                cases.selectCount(new QueryWrapper<TestCase>().eq("problem_id", input.problem()))
                        > 0,
                400,
                "No testcases configured");
        abuse.limit("submit:" + actor.id, 5, 60, 1000);
        var s = new Submission();
        s.userId = actor.id;
        s.problemId = input.problem();
        s.contestId = input.contest();
        s.language = input.language();
        s.code = input.code();
        s.codeSize = size;
        s.verdict = "PENDING";
        s.score = 0;
        s.maxTimeMs = 0;
        s.maxMemoryKb = 0;
        s.compileMessage = "";
        s.judgeAttempts = 0;
        s.submittedAt = Instant.now();
        submissions.insert(s);
        var event = new JudgeOutbox();
        event.submissionId = s.id;
        event.createdAt = Instant.now();
        outbox.insert(event);
        return view(s, actor, false);
    }

    public Object list(
            User actor,
            Long problem,
            Long contest,
            String language,
            String verdict,
            int page,
            Long author) {
        var q = new QueryWrapper<Submission>();
        if (author != null) q.eq("user_id", author);
        if (!CurrentUser.staff(actor)) {
            if (problem == null) q.eq("user_id", actor.id);
            else contests.readableProblem(problem, contest, actor);
            q.and(
                    visible ->
                            visible.eq("user_id", actor.id)
                                    .or()
                                    .isNull("contest_id")
                                    .or()
                                    .apply(
                                            """
                                            EXISTS (SELECT 1 FROM contest c
                                                WHERE c.id = submission.contest_id AND
                                                (c.is_public = TRUE OR c.created_by = {0} OR EXISTS
                                                    (SELECT 1 FROM contest_participant cp
                                                     WHERE cp.contest_id = c.id AND cp.user_id = {0})))
                                            """,
                                            actor.id));
        }
        if (problem != null) q.eq("problem_id", problem);
        if (contest != null) {
            contests.get(contest, actor);
            q.eq("contest_id", contest);
        }
        if (language != null) q.eq("language", language);
        if (verdict != null) q.eq("verdict", verdict);
        long count = submissions.selectCount(q);
        return Map.of(
                "count",
                count,
                "results",
                submissions
                        .selectList(
                                q.orderByDesc("id")
                                        .last("LIMIT 30 OFFSET " + ((Math.max(1, page) - 1) * 30L)))
                        .stream()
                        .map(s -> view(s, actor, false))
                        .toList());
    }

    public Object detail(Long id, User actor) {
        var s = submissions.selectById(id);
        ApiException.require(s != null, 404, "Submission not found");
        ApiException.require(
                CurrentUser.staff(actor) || s.userId.equals(actor.id),
                403,
                "Submission detail is private");
        return view(s, actor, true);
    }

    public Map<String, Object> view(Submission s, User actor, boolean detail) {
        var v = json.view(s);
        v.remove("lease_token");
        v.remove("lease_until");
        v.remove("judge_attempts");
        v.put("user", s.userId);
        v.put("problem", s.problemId);
        v.put("contest", s.contestId);
        v.put("username", users.selectById(s.userId).username);
        v.put("problem_title", problems.selectById(s.problemId).title);
        if (!detail) v.remove("compile_message");
        if (detail) {
            v.put("code", s.code);
            v.put(
                    "case_results",
                    results
                            .selectList(
                                    new QueryWrapper<CaseResult>()
                                            .eq("submission_id", s.id)
                                            .orderByAsc("case_id"))
                            .stream()
                            .map(
                                    r -> {
                                        var item = json.view(r);
                                        if (!CurrentUser.staff(actor)) {
                                            item.remove("stdout");
                                            item.remove("stderr");
                                            item.remove("case_id");
                                            item.remove("message");
                                        }
                                        return item;
                                    })
                            .toList());
        }
        return v;
    }
}
