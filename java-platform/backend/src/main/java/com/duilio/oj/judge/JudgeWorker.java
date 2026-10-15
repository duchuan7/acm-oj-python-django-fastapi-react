package com.duilio.oj.judge;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.duilio.oj.config.QueueConfig;
import com.duilio.oj.mapper.*;
import com.duilio.oj.model.*;

import org.slf4j.*;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
@ConditionalOnProperty(name = "oj.mode", havingValue = "judge")
public class JudgeWorker {
    private static final Logger log = LoggerFactory.getLogger(JudgeWorker.class);
    private final JudgeJobs jobs;
    private final ProblemMapper problems;
    private final TestCaseMapper tests;
    private final DockerSandbox sandbox;

    public JudgeWorker(
            JudgeJobs jobs, ProblemMapper problems, TestCaseMapper tests, DockerSandbox sandbox) {
        this.jobs = jobs;
        this.problems = problems;
        this.tests = tests;
        this.sandbox = sandbox;
    }

    @RabbitListener(queues = QueueConfig.QUEUE)
    public void receive(String message) {
        Long id;
        try {
            id = Long.valueOf(message);
        } catch (NumberFormatException e) {
            throw new org.springframework.amqp.AmqpRejectAndDontRequeueException(
                    "Invalid submission id");
        }
        Submission s = jobs.claim(id);
        if (s == null) return;
        DockerSandbox.Outcome outcome;
        var heartbeat =
                java.util.concurrent.Executors.newSingleThreadScheduledExecutor(
                        Thread.ofVirtual().factory());
        heartbeat.scheduleAtFixedRate(
                () -> {
                    try {
                        jobs.heartbeat(s);
                    } catch (Exception e) {
                        log.warn("Heartbeat failed for submission {}", id);
                    }
                },
                30,
                30,
                java.util.concurrent.TimeUnit.SECONDS);
        try {
            outcome =
                    sandbox.judge(
                            s,
                            problems.selectById(s.problemId),
                            tests.selectList(
                                    new QueryWrapper<TestCase>()
                                            .eq("problem_id", s.problemId)
                                            .orderByAsc("case_order")));
        } catch (Exception e) {
            log.error("Sandbox failed for submission {}", id, e);
            outcome =
                    new DockerSandbox.Outcome(
                            "SYSTEM_ERROR",
                            0,
                            0,
                            0,
                            "Judge infrastructure failed; contact administrator",
                            List.of());
        } finally {
            heartbeat.shutdownNow();
        }
        jobs.finish(s, outcome);
    }
}
