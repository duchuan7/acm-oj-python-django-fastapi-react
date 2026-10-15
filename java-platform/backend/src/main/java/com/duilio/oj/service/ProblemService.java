package com.duilio.oj.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.duilio.oj.common.*;
import com.duilio.oj.dto.Requests.ProblemDraft;
import com.duilio.oj.mapper.*;
import com.duilio.oj.model.*;
import com.duilio.oj.security.CurrentUser;

import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.*;
import java.util.*;

@Service
public class ProblemService {
    private final ProblemMapper problems;
    private final TestCaseMapper cases;
    private final SubmissionMapper submissions;
    private final StatisticsMapper stats;
    private final StringRedisTemplate redis;
    private final Json json;

    public ProblemService(
            ProblemMapper problems,
            TestCaseMapper cases,
            SubmissionMapper submissions,
            StatisticsMapper stats,
            StringRedisTemplate redis,
            Json json) {
        this.problems = problems;
        this.cases = cases;
        this.submissions = submissions;
        this.stats = stats;
        this.redis = redis;
        this.json = json;
    }

    public Problem get(Long id) {
        Problem problem = problems.selectById(id);
        ApiException.require(problem != null, 404, "Problem not found");
        return problem;
    }

    public Object list(String search, String tag, Integer min, Integer max, int page, User actor) {
        var q = new QueryWrapper<Problem>();
        if (!CurrentUser.staff(actor)) q.eq("is_public", true);
        if (search != null && !search.isBlank())
            q.and(
                    w ->
                            w.like("title", search)
                                    .or()
                                    .like("slug", search)
                                    .or()
                                    .like("source", search));
        if (min != null) q.ge("difficulty", min);
        if (max != null) q.le("difficulty", max);
        // Tags use a bound JSON parameter; the MySQL JSON function matches an exact tag.
        if (tag != null && !tag.isBlank()) q.apply("JSON_CONTAINS(tags, {0})", json.write(tag));
        long count = problems.selectCount(q);
        q.orderByAsc("id").last("LIMIT 30 OFFSET " + ((Math.max(1, page) - 1) * 30L));
        return Map.of(
                "count",
                count,
                "results",
                problems.selectList(q).stream().map(p -> view(p, false)).toList());
    }

    public Map<String, Object> view(Problem problem, boolean management) {
        var result = json.view(problem);
        result.putAll(stats.problemStats(problem.id));
        if (management)
            result.put(
                    "test_cases",
                    cases.selectList(
                            new QueryWrapper<TestCase>()
                                    .eq("problem_id", problem.id)
                                    .orderByAsc("case_order")));
        return result;
    }

    public Object cachedView(Problem problem, boolean management) {
        if (management || !problem.isPublic) return view(problem, management);
        String key = "oj:problem:" + problem.id + ":" + problem.updatedAt.toEpochMilli();
        try {
            String cached = redis.opsForValue().get(key);
            if (cached != null) return json.read(cached, Map.class);
            var result = view(problem, false);
            redis.opsForValue().set(key, json.write(result), Duration.ofSeconds(30));
            return result;
        } catch (org.springframework.data.redis.RedisConnectionFailureException e) {
            return view(problem, false);
        }
    }

    @Transactional
    public Problem save(Long id, ProblemDraft input, User actor, Boolean forcedPublic) {
        Problem p = id == null ? new Problem() : get(id);
        if (id == null) {
            p.createdBy = actor.id;
            p.createdAt = Instant.now();
        }
        p.title = input.title();
        p.slug = input.slug();
        p.description = input.description();
        p.inputDescription = input.inputDescription();
        p.outputDescription = input.outputDescription();
        p.samples = input.samples();
        p.timeLimitMs = input.timeLimitMs();
        p.memoryLimitMb = input.memoryLimitMb();
        p.difficulty = input.difficulty();
        p.tags = input.tags();
        p.source = input.source();
        p.isPublic = forcedPublic == null ? input.isPublic() : forcedPublic;
        p.updatedAt = Instant.now();
        ApiException.require(
                !input.testCases().isEmpty(), 400, "At least one testcase is required");
        ApiException.require(
                input.testCases().stream().map(c -> c.order()).distinct().count()
                        == input.testCases().size(),
                400,
                "Duplicate testcase order");
        ApiException.require(
                input.testCases().stream().mapToInt(c -> c.score()).sum() == 100,
                400,
                "Testcase scores must add up to 100");
        if (id == null) problems.insert(p);
        else problems.updateById(p);
        var existing =
                cases.selectList(
                        new QueryWrapper<TestCase>()
                                .eq("problem_id", p.id)
                                .orderByAsc("case_order"));
        boolean changed = existing.size() != input.testCases().size();
        if (!changed)
            for (int i = 0; i < existing.size(); i++) {
                var a = existing.get(i);
                var b =
                        input.testCases().stream()
                                .sorted(Comparator.comparing(c -> c.order()))
                                .toList()
                                .get(i);
                if (!a.caseOrder.equals(b.order())
                        || !a.inputText.equals(b.input())
                        || !a.outputText.equals(b.output())
                        || !a.score.equals(b.score())
                        || a.isSample != b.isSample()) changed = true;
            }
        if (changed) {
            ApiException.require(
                    submissions.selectCount(new QueryWrapper<Submission>().eq("problem_id", p.id))
                            == 0,
                    409,
                    "Testcases are immutable after submissions; create a new problem version");
            cases.delete(new QueryWrapper<TestCase>().eq("problem_id", p.id));
            for (var item : input.testCases()) {
                var c = new TestCase();
                c.problemId = p.id;
                c.caseOrder = item.order();
                c.inputText = item.input();
                c.outputText = item.output();
                c.score = item.score();
                c.isSample = item.isSample();
                cases.insert(c);
            }
        }
        return p;
    }

    @Transactional
    public void delete(Long id) {
        get(id);
        cases.delete(new QueryWrapper<TestCase>().eq("problem_id", id));
        problems.deleteById(id);
    }
}
