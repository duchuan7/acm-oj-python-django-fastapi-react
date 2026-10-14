package com.duilio.oj.service;

import java.time.Duration;
import java.util.*;
import com.duilio.oj.model.*;
import com.duilio.oj.mapper.UserMapper;

public final class Rankings {
    private Rankings() {}
    public static List<Map<String,Object>> build(Contest contest,List<Submission> submissions,List<ContestProblem> links,UserMapper users) {
        Map<Long,Integer> weights=new HashMap<>(); for(var link:links) weights.put(link.problemId,link.score);
        Map<Long,List<Submission>> byUser=new LinkedHashMap<>();
        for(var s:submissions) byUser.computeIfAbsent(s.userId,k->new ArrayList<>()).add(s);
        List<Map<String,Object>> rows=new ArrayList<>();
        byUser.forEach((uid,attempts)->{
            Map<Long,List<Submission>> byProblem=new HashMap<>();
            for(var s:attempts) byProblem.computeIfAbsent(s.problemId,k->new ArrayList<>()).add(s);
            int solved=0,score=0,penalty=0;
            for(var group:byProblem.values()) {
                if("ACM".equals(contest.rule)) {
                    int wrong=0;
                    for(var s:group) {
                        if("ACCEPTED".equals(s.verdict)) {
                            solved++; penalty+=(int)Duration.between(contest.startAt,s.submittedAt).toMinutes()+wrong*20; break;
                        }
                        if("WRONG_ANSWER".equals(s.verdict)) wrong++;
                    }
                } else {
                    var best=group.stream().max(Comparator.comparingInt(s->s.score)).orElseThrow();
                    int value=best.score*weights.getOrDefault(best.problemId,100)/100;
                    score+=value;
                    if(value>0) { solved++; penalty+=(int)Duration.between(contest.startAt,best.submittedAt).toMinutes(); }
                }
            }
            var row=new LinkedHashMap<String,Object>(); row.put("user_id",uid); row.put("username",users.selectById(uid).username);
            row.put("solved",solved); row.put("score",score); row.put("penalty_minutes",penalty); rows.add(row);
        });
        String primary="IOI".equals(contest.rule)?"score":"solved";
        rows.sort(Comparator.<Map<String,Object>>comparingInt(r->-((Number)r.get(primary)).intValue())
            .thenComparingInt(r->((Number)r.get("penalty_minutes")).intValue())
            .thenComparingLong(r->((Number)r.get("user_id")).longValue()));
        for(int i=0;i<rows.size();i++) rows.get(i).put("rank",i+1);
        return rows;
    }
}

