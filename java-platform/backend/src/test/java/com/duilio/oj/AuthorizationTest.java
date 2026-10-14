package com.duilio.oj;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.jwt;
import static org.mockito.Mockito.*;
import java.time.Instant;
import com.duilio.oj.mapper.*;
import com.duilio.oj.model.*;
import com.duilio.oj.service.AbuseService;
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.data.redis.core.*;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

@SpringBootTest(properties={
    "spring.datasource.url=jdbc:h2:mem:ojtest;MODE=MySQL;DATABASE_TO_LOWER=TRUE;DB_CLOSE_DELAY=-1",
    "spring.datasource.username=sa","spring.datasource.password=",
    "spring.flyway.enabled=false","spring.sql.init.mode=always",
    "spring.sql.init.schema-locations=classpath:db/migration/V1__initial.sql",
    "oj.jwt-secret=unit-test-secret-with-at-least-32-bytes",
    "oj.admin-password=","oj.seed-demo=false","oj.jobs.enabled=false","spring.rabbitmq.dynamic=false"
})
@AutoConfigureMockMvc
@Transactional
class AuthorizationTest {
    @Autowired MockMvc mvc;
    @Autowired UserMapper users;
    @Autowired ProblemMapper problems;
    @Autowired SubmissionMapper submissions;
    @Autowired ProblemSolutionMapper solutions;
    @MockitoBean StringRedisTemplate redis;
    @MockitoBean AbuseService abuse;
    private User admin,member,other;
    private Problem hidden,pub;
    @BeforeEach void fixtures() {
        when(redis.opsForValue()).thenReturn(mock(ValueOperations.class));
        admin=user("admin","ADMIN"); member=user("member","MEMBER"); other=user("other","MEMBER");
        pub=problem("public",true); hidden=problem("secret",false);
    }
    private User user(String name,String role) {
        var u=new User(); u.username=name; u.password="unused"; u.role=role; u.active=true; u.tokenVersion=0;
        u.school=""; u.realName=""; u.createdAt=Instant.now(); users.insert(u); return u;
    }
    private Problem problem(String slug,boolean visible) {
        var p=new Problem(); p.title=slug; p.slug=slug; p.description="statement"; p.inputDescription="in";
        p.outputDescription="out"; p.samples=java.util.List.of(); p.tags=java.util.List.of();
        p.timeLimitMs=1000; p.memoryLimitMb=256; p.source=""; p.isPublic=visible; p.createdBy=admin.id;
        p.createdAt=Instant.now(); p.updatedAt=p.createdAt; problems.insert(p); return p;
    }
    @Test void anonymousCannotSubmitAndMemberCannotManageProblems() throws Exception {
        mvc.perform(post("/api/submissions").contentType("application/json").content("{}")).andExpect(status().isUnauthorized());
        mvc.perform(delete("/api/problems/"+pub.id).with(jwt().jwt(j->j.subject(member.id.toString())))).andExpect(status().isForbidden());
    }
    @Test void hiddenProblemCannotBeEnumerated() throws Exception {
        mvc.perform(get("/api/problems/"+hidden.id)).andExpect(status().isNotFound());
        mvc.perform(get("/api/problems")).andExpect(status().isOk()).andExpect(jsonPath("$.count").value(1));
    }
    @Test void publicProblemDoesNotExposeTestcases() throws Exception {
        mvc.perform(get("/api/problems/"+pub.id)).andExpect(status().isOk()).andExpect(jsonPath("$.test_cases").doesNotExist());
    }
    @Test void anotherMembersSubmissionIsPrivate() throws Exception {
        var s=new Submission(); s.userId=member.id; s.problemId=pub.id; s.language="CPP"; s.code="private source";
        s.codeSize=14; s.verdict="PENDING"; s.score=0; s.maxTimeMs=0; s.maxMemoryKb=0; s.compileMessage="";
        s.judgeAttempts=0; s.submittedAt=Instant.now(); submissions.insert(s);
        mvc.perform(get("/api/submissions/"+s.id).with(jwt().jwt(j->j.subject(other.id.toString())))).andExpect(status().isForbidden());
    }
    @Test void memberCannotApproveEditorial() throws Exception {
        mvc.perform(post("/api/problem-solutions/1/approve").with(jwt().jwt(j->j.subject(member.id.toString())))
            .contentType("application/json").content("{}")).andExpect(status().isForbidden());
    }
    @Test void publicContestRequiresAdminEvenForCoach() throws Exception {
        String body="""
            {"title":"unauthorized","description":"","rule":"ACM","start_at":"2026-01-01T00:00:00Z",
            "end_at":"2026-01-01T01:00:00Z","is_public":true,"freeze_rank_minutes":0,"participants":[],"contest_problems":[]}
            """;
        mvc.perform(post("/api/contests").with(jwt().jwt(j->j.subject(member.id.toString())))
            .contentType("application/json").content(body)).andExpect(status().isForbidden());
    }
}

