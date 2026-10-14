package com.duilio.oj.judge;

import java.time.Instant;
import java.util.*;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.UpdateWrapper;
import com.duilio.oj.mapper.*;
import com.duilio.oj.model.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class JudgeJobs {
    private final SubmissionMapper submissions;
    private final CaseResultMapper results;
    public JudgeJobs(SubmissionMapper submissions,CaseResultMapper results) { this.submissions=submissions; this.results=results; }
    public Submission claim(Long id) {
        String token=UUID.randomUUID().toString();
        int changed=submissions.update(new UpdateWrapper<Submission>().eq("id",id).eq("verdict","PENDING")
            .set("verdict","JUDGING").set("lease_token",token).set("lease_until",Instant.now().plusSeconds(240))
            .setSql("judge_attempts = judge_attempts + 1"));
        return changed==1?submissions.selectById(id):null;
    }
    @Transactional
    public void finish(Submission s,DockerSandbox.Outcome outcome) {
        int changed=submissions.update(new UpdateWrapper<Submission>().eq("id",s.id).eq("verdict","JUDGING").eq("lease_token",s.leaseToken)
            .set("verdict",outcome.verdict()).set("score",outcome.score()).set("max_time_ms",outcome.timeMs())
            .set("max_memory_kb",outcome.memoryKb()).set("compile_message",outcome.compileMessage())
            .set("judged_at",Instant.now()).set("lease_token",null).set("lease_until",null));
        if(changed!=1) return; // A stale delivery must never overwrite a later attempt.
        results.delete(new QueryWrapper<CaseResult>().eq("submission_id",s.id));
        for(var result:outcome.cases()) { result.submissionId=s.id; results.insert(result); }
    }
    public void heartbeat(Submission s) {
        submissions.update(new UpdateWrapper<Submission>().eq("id",s.id).eq("verdict","JUDGING")
            .eq("lease_token",s.leaseToken).set("lease_until",Instant.now().plusSeconds(240)));
    }
}

