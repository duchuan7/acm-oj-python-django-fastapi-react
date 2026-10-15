package com.duilio.oj;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

import com.duilio.oj.judge.OutputComparator;
import com.duilio.oj.mapper.UserMapper;
import com.duilio.oj.model.*;
import com.duilio.oj.security.Passwords;
import com.duilio.oj.service.Rankings;

import org.junit.jupiter.api.Test;

import java.nio.charset.StandardCharsets;
import java.util.*;

import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;

class CoreRulesTest {
    @Test
    void outputComparisonPreservesLeadingWhitespaceAndIgnoresLineEndings() {
        assertTrue(OutputComparator.matches("3\r\n", "3  \n\n"));
        assertFalse(OutputComparator.matches("3\n", " 3\n"));
        assertFalse(OutputComparator.matches("1 2", "12"));
    }

    @Test
    void djangoPasswordCanBeVerifiedAndWrongPasswordRejected() throws Exception {
        var key =
                SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256")
                        .generateSecret(
                                new PBEKeySpec(
                                        "old-password".toCharArray(),
                                        "legacy-salt".getBytes(StandardCharsets.UTF_8),
                                        600000,
                                        256))
                        .getEncoded();
        String hash = "pbkdf2_sha256$600000$legacy-salt$" + Base64.getEncoder().encodeToString(key);
        var passwords = new Passwords();
        assertTrue(passwords.matches("old-password", hash));
        assertFalse(passwords.matches("bad-password", hash));
        assertFalse(passwords.matches("old-password", "pbkdf2_sha256$broken"));
    }

    @Test
    void acmRankUsesFirstAcceptedAndWrongAnswersBeforeAcceptance() {
        var contest = new Contest();
        contest.rule = "ACM";
        contest.startAt = java.time.Instant.parse("2026-01-01T00:00:00Z");
        var users = mock(UserMapper.class);
        var u = new User();
        u.id = 1L;
        u.username = "alice";
        when(users.selectById(1L)).thenReturn(u);
        var attempts = new ArrayList<Submission>();
        String[] verdicts = {
            "WRONG_ANSWER", "COMPILE_ERROR", "ACCEPTED", "WRONG_ANSWER", "ACCEPTED"
        };
        for (int i = 0; i < verdicts.length; i++) {
            var s = new Submission();
            s.id = (long) i;
            s.userId = 1L;
            s.problemId = 1L;
            s.verdict = verdicts[i];
            s.score = 0;
            s.submittedAt = contest.startAt.plusSeconds((i + 1) * 60L);
            attempts.add(s);
        }
        var row = Rankings.build(contest, attempts, List.of(), users).getFirst();
        assertEquals(1, row.get("solved"));
        assertEquals(23, row.get("penalty_minutes"));
    }

    @Test
    void ioiRankUsesBestScoreAndContestWeight() {
        var c = new Contest();
        c.rule = "IOI";
        c.startAt = java.time.Instant.EPOCH;
        var mapper = mock(UserMapper.class);
        var u = new User();
        u.id = 1L;
        u.username = "bob";
        when(mapper.selectById(1L)).thenReturn(u);
        var a = new Submission();
        a.userId = 1L;
        a.problemId = 2L;
        a.score = 60;
        a.submittedAt = c.startAt.plusSeconds(120);
        var b = new Submission();
        b.userId = 1L;
        b.problemId = 2L;
        b.score = 20;
        b.submittedAt = c.startAt.plusSeconds(180);
        var link = new ContestProblem();
        link.problemId = 2L;
        link.score = 50;
        var row = Rankings.build(c, List.of(a, b), List.of(link), mapper).getFirst();
        assertEquals(30, row.get("score"));
        assertEquals(2, row.get("penalty_minutes"));
    }
}
