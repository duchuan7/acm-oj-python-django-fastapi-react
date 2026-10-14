package com.duilio.oj.service;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.duilio.oj.dto.Requests.*;
import com.duilio.oj.mapper.*;
import com.duilio.oj.model.User;
import com.duilio.oj.security.Passwords;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

@Component
@Profile("!judge")
public class DemoData implements ApplicationRunner {
    private final UserMapper users;
    private final ProblemMapper problems;
    private final ProblemService problemService;
    private final Passwords passwords;
    private final String username,password;
    private final boolean seed;
    public DemoData(UserMapper users,ProblemMapper problems,ProblemService problemService,Passwords passwords,
        @Value("${oj.admin-username}") String username,@Value("${oj.admin-password}") String password,@Value("${oj.seed-demo}") boolean seed) {
        this.users=users; this.problems=problems; this.problemService=problemService; this.passwords=passwords;
        this.username=username; this.password=password; this.seed=seed;
    }
    @Transactional
    public void run(ApplicationArguments args) {
        if(password.isBlank()) return;
        User admin=users.selectOne(new QueryWrapper<User>().eq("username",username));
        if(admin==null) {
            admin=new User(); admin.username=username; admin.email=null; admin.password=passwords.encode(password);
            admin.role="ADMIN"; admin.active=true; admin.tokenVersion=0; admin.school=""; admin.realName="";
            admin.createdAt=Instant.now(); users.insert(admin);
        }
        if(seed&&problems.selectCount(new QueryWrapper<>())==0) {
            var draft=new ProblemDraft("A + B","a-plus-b","计算两个整数的和。Compute the sum of two integers.",
                "两个整数 a 和 b，绝对值不超过 10^9。","输出 a + b。",
                List.of(Map.of("input","1 2\n","output","3\n")),1000,256,800,List.of("入门","math"),"duilio OJ",true,
                List.of(new CaseDraft(1,"1 2\n","3\n",50,true),new CaseDraft(2,"-100 42\n","-58\n",50,false)));
            problemService.save(null,draft,admin,null);
        }
    }
}

