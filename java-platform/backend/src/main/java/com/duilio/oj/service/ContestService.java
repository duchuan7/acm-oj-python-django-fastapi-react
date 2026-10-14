package com.duilio.oj.service;

import java.time.*;
import java.util.*;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.UpdateWrapper;
import com.duilio.oj.common.*;
import com.duilio.oj.dto.Requests.ContestDraft;
import com.duilio.oj.mapper.*;
import com.duilio.oj.model.*;
import com.duilio.oj.security.CurrentUser;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ContestService {
    private final ContestMapper contests;
    private final ContestProblemMapper links;
    private final ContestParticipantMapper participants;
    private final ProblemMapper problems;
    private final SubmissionMapper submissions;
    private final UserMapper users;
    private final ProblemService problemService;
    private final Json json;
    public ContestService(ContestMapper contests,ContestProblemMapper links,ContestParticipantMapper participants,
        ProblemMapper problems,SubmissionMapper submissions,UserMapper users,ProblemService problemService,Json json) {
        this.contests=contests; this.links=links; this.participants=participants; this.problems=problems;
        this.submissions=submissions; this.users=users; this.problemService=problemService; this.json=json;
    }
    public boolean owner(Contest c,User u) { return u!=null&&(CurrentUser.staff(u)||u.id.equals(c.createdBy)); }
    public boolean visible(Contest c,User u) {
        return c.isPublic||owner(c,u)||(u!=null&&participants.selectCount(new QueryWrapper<ContestParticipant>().eq("contest_id",c.id).eq("user_id",u.id))>0);
    }
    public Contest get(Long id,User actor) {
        Contest c=contests.selectById(id); ApiException.require(c!=null&&visible(c,actor),404,"Contest not found"); return c;
    }
    @Transactional
    public void publishFinished() {
        for(var c:contests.selectList(new QueryWrapper<Contest>().le("end_at",Instant.now()))) {
            for(var link:links.selectList(new QueryWrapper<ContestProblem>().eq("contest_id",c.id).eq("created_for_contest",true)))
                problems.update(new UpdateWrapper<Problem>().eq("id",link.problemId).eq("is_public",false).set("is_public",true).set("updated_at",Instant.now()));
        }
    }
    public Object list(User actor,String visibility) {
        publishFinished();
        var q=new QueryWrapper<Contest>().orderByDesc("start_at");
        if("public".equals(visibility)) q.eq("is_public",true);
        if("private".equals(visibility)) q.eq("is_public",false);
        return contests.selectList(q.last("LIMIT 500")).stream().filter(c->visible(c,actor)).map(c->view(c,actor)).toList();
    }
    public Object view(Contest c,User actor) {
        var result=json.view(c);
        result.put("participants",participants.selectList(new QueryWrapper<ContestParticipant>().eq("contest_id",c.id)).stream().map(p->p.userId).toList());
        if(owner(c,actor)||!Instant.now().isBefore(c.startAt)) result.put("contest_problems",
            links.selectList(new QueryWrapper<ContestProblem>().eq("contest_id",c.id).orderByAsc("problem_order")).stream().map(link->{
                var v=json.view(link); v.put("problem",link.problemId); v.put("order",link.problemOrder);
                v.put("problem_detail",problemService.view(problemService.get(link.problemId),false)); return v;
            }).toList());
        else result.put("contest_problems",List.of());
        return result;
    }
    public Problem readableProblem(Long id,Long contestId,User actor) {
        publishFinished(); var p=problemService.get(id);
        if(p.isPublic||CurrentUser.staff(actor)) return p;
        ApiException.require(contestId!=null,404,"Problem not found");
        var c=get(contestId,actor);
        ApiException.require(owner(c,actor)||!Instant.now().isBefore(c.startAt),404,"Problem not available before contest");
        ApiException.require(links.selectCount(new QueryWrapper<ContestProblem>().eq("contest_id",contestId).eq("problem_id",id))>0,404,"Problem not in contest");
        return p;
    }
    public void validateSubmission(Long problemId,Long contestId,User actor) {
        var p=problemService.get(problemId);
        if(contestId==null) { ApiException.require(p.isPublic||CurrentUser.staff(actor),403,"Problem is private"); return; }
        var c=get(contestId,actor); var now=Instant.now();
        ApiException.require(!now.isBefore(c.startAt)&&now.isBefore(c.endAt),400,"Contest is not accepting submissions");
        ApiException.require(links.selectCount(new QueryWrapper<ContestProblem>().eq("contest_id",c.id).eq("problem_id",problemId))>0,400,"Problem is not in contest");
    }
    @Transactional
    public Contest save(Long id,ContestDraft input,User actor) {
        Contest c=id==null?new Contest():get(id,actor);
        ApiException.require(id==null||owner(c,actor),403,"Contest owner required");
        ApiException.require(!input.isPublic()||CurrentUser.admin(actor),403,"Only admins can make contests public");
        ApiException.require(input.endAt().isAfter(input.startAt()),400,"End must be after start");
        if(id!=null) ApiException.require(submissions.selectCount(new QueryWrapper<Submission>().eq("contest_id",id))==0,409,"Contest is immutable after submissions");
        if(id==null) { c.createdBy=actor.id; c.createdAt=Instant.now(); }
        c.title=input.title(); c.description=input.description(); c.rule=input.rule(); c.startAt=input.startAt(); c.endAt=input.endAt();
        c.isPublic=input.isPublic(); c.freezeRankMinutes=input.freezeRankMinutes();
        if(id==null) contests.insert(c); else contests.updateById(c);
        links.delete(new QueryWrapper<ContestProblem>().eq("contest_id",c.id));
        participants.delete(new QueryWrapper<ContestParticipant>().eq("contest_id",c.id));
        for(Long uid:new HashSet<>(input.participants())) {
            ApiException.require(users.selectById(uid)!=null,400,"Unknown participant");
            var p=new ContestParticipant(); p.contestId=c.id; p.userId=uid; participants.insert(p);
        }
        for(var item:input.contestProblems()) {
            ApiException.require((item.problem()!=null) != (item.newProblem()!=null),400,"Choose existing problem or new problem");
            Long pid;
            if(item.newProblem()!=null) pid=problemService.save(null,item.newProblem(),actor,false).id;
            else { var p=problemService.get(item.problem()); ApiException.require(p.isPublic||CurrentUser.staff(actor),403,"Cannot add a private problem"); pid=p.id; }
            var link=new ContestProblem(); link.contestId=c.id; link.problemId=pid; link.alias=item.alias();
            link.problemOrder=item.order(); link.score=item.score(); link.createdForContest=item.newProblem()!=null; links.insert(link);
        }
        return c;
    }
    @Transactional
    public void delete(Long id,User actor) {
        var c=get(id,actor); ApiException.require(owner(c,actor),403,"Contest owner required");
        links.delete(new QueryWrapper<ContestProblem>().eq("contest_id",id));
        participants.delete(new QueryWrapper<ContestParticipant>().eq("contest_id",id)); contests.deleteById(id);
    }
    public Object ranklist(Long id,User actor) {
        var c=get(id,actor);
        Instant cutoff=c.endAt;
        boolean frozen=c.freezeRankMinutes>0&&Instant.now().isBefore(c.endAt)&&!Instant.now().isBefore(c.endAt.minusSeconds(c.freezeRankMinutes*60L));
        if(frozen) cutoff=c.endAt.minusSeconds(c.freezeRankMinutes*60L);
        var rows=submissions.selectList(new QueryWrapper<Submission>().eq("contest_id",id).ge("submitted_at",c.startAt)
            .lt("submitted_at",cutoff).orderByAsc("submitted_at","id"));
        return Map.of("frozen",frozen,"results",Rankings.build(c,rows,links.selectList(new QueryWrapper<ContestProblem>().eq("contest_id",id)),users));
    }
}

