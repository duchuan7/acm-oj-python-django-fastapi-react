package com.duilio.oj.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.UpdateWrapper;
import com.duilio.oj.config.QueueConfig;
import com.duilio.oj.mapper.*;
import com.duilio.oj.model.*;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.rabbit.connection.CorrelationData;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.boot.autoconfigure.condition.ConditionalOnExpression;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.support.TransactionTemplate;

import java.time.Instant;
import java.util.concurrent.TimeUnit;

@Component
@ConditionalOnExpression("'${oj.mode:api}' == 'api' && ${oj.jobs.enabled:true}")
public class OutboxDispatcher {
    private static final Logger log = LoggerFactory.getLogger(OutboxDispatcher.class);
    private final JudgeOutboxMapper outbox;
    private final SubmissionMapper submissions;
    private final RabbitTemplate rabbit;
    private final TransactionTemplate tx;

    public OutboxDispatcher(
            JudgeOutboxMapper outbox,
            SubmissionMapper submissions,
            RabbitTemplate rabbit,
            TransactionTemplate tx) {
        this.outbox = outbox;
        this.submissions = submissions;
        this.rabbit = rabbit;
        this.tx = tx;
    }

    @Scheduled(fixedDelay = 2000)
    public void dispatch() {
        for (var event :
                outbox.selectList(
                        new QueryWrapper<JudgeOutbox>()
                                .isNull("sent_at")
                                .orderByAsc("id")
                                .last("LIMIT 30"))) {
            try {
                var correlation = new CorrelationData(event.id.toString());
                rabbit.convertAndSend(
                        "", QueueConfig.QUEUE, event.submissionId.toString(), correlation);
                var confirm = correlation.getFuture().get(5, TimeUnit.SECONDS);
                if (!confirm.isAck() || correlation.getReturned() != null) break;
                outbox.update(
                        new UpdateWrapper<JudgeOutbox>()
                                .eq("id", event.id)
                                .isNull("sent_at")
                                .set("sent_at", Instant.now()));
            } catch (Exception e) {
                log.warn("Judge queue unavailable; outbox {} retained", event.id);
                break;
            }
        }
    }

    @Scheduled(fixedDelay = 30000)
    public void recoverExpired() {
        for (var s :
                submissions.selectList(
                        new QueryWrapper<Submission>()
                                .eq("verdict", "JUDGING")
                                .lt("lease_until", Instant.now())
                                .last("LIMIT 30"))) {
            tx.executeWithoutResult(
                    ignored -> {
                        boolean exhausted = s.judgeAttempts >= 3;
                        int changed =
                                submissions.update(
                                        new UpdateWrapper<Submission>()
                                                .eq("id", s.id)
                                                .eq("verdict", "JUDGING")
                                                .eq("lease_token", s.leaseToken)
                                                .lt("lease_until", Instant.now())
                                                .set(
                                                        "verdict",
                                                        exhausted ? "SYSTEM_ERROR" : "PENDING")
                                                .set("lease_token", null)
                                                .set("lease_until", null)
                                                .set(exhausted, "judged_at", Instant.now())
                                                .set(
                                                        exhausted,
                                                        "compile_message",
                                                        "Judge worker repeatedly interrupted"));
                        if (changed == 1 && !exhausted) {
                            var event = new JudgeOutbox();
                            event.submissionId = s.id;
                            event.createdAt = Instant.now();
                            outbox.insert(event);
                        }
                    });
        }
    }
}
