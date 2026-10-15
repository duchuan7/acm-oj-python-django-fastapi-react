package com.duilio.oj.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.UpdateWrapper;
import com.duilio.oj.common.ApiException;
import com.duilio.oj.dto.Requests.UserUpdate;
import com.duilio.oj.mapper.*;
import com.duilio.oj.model.*;
import com.duilio.oj.security.CurrentUser;
import com.duilio.oj.service.AuthService;

import jakarta.validation.Valid;

import org.springframework.context.annotation.Profile;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@RestController
@RequestMapping("/api/users")
@Profile("!judge")
public class UserController {
    private final UserMapper users;
    private final StatisticsMapper stats;
    private final BlogPostMapper blogs;
    private final CurrentUser current;

    public UserController(
            UserMapper users, StatisticsMapper stats, BlogPostMapper blogs, CurrentUser current) {
        this.users = users;
        this.stats = stats;
        this.blogs = blogs;
        this.current = current;
    }

    @GetMapping
    Object list() {
        var actor = current.required();
        return users
                .selectList(new QueryWrapper<User>().orderByAsc("id").last("LIMIT 500"))
                .stream()
                .map(
                        u ->
                                CurrentUser.admin(actor)
                                        ? AuthService.privateView(u)
                                        : AuthService.publicView(u))
                .toList();
    }

    @GetMapping("/leaderboard")
    Object leaderboard() {
        return stats.leaderboard();
    }

    @GetMapping("/{id}/profile")
    Object profile(@PathVariable Long id) {
        User user = users.selectById(id);
        ApiException.require(user != null, 404, "User not found");
        return Map.of(
                "user",
                AuthService.publicView(user),
                "stats",
                stats.userStats(id),
                "submissions",
                stats.profileSubmissions(id),
                "blogs",
                blogs.selectList(
                        new QueryWrapper<BlogPost>()
                                .eq("author_id", id)
                                .eq("status", "PUBLISHED")
                                .orderByDesc("id")
                                .last("LIMIT 50")));
    }

    @PatchMapping("/{id}")
    Object update(@PathVariable Long id, @Valid @RequestBody UserUpdate input) {
        var actor = current.requireAdmin();
        var user = users.selectById(id);
        ApiException.require(user != null, 404, "User not found");
        ApiException.require(
                !actor.id.equals(id)
                        || ((input.active() == null || input.active())
                                && (input.role() == null || input.role().equals("ADMIN"))),
                400,
                "Cannot remove your own admin access");
        users.update(
                new UpdateWrapper<User>()
                        .eq("id", id)
                        .set(input.role() != null, "role", input.role())
                        .set(input.active() != null, "active", input.active())
                        .set(input.school() != null, "school", input.school())
                        .set(input.realName() != null, "real_name", input.realName())
                        .setSql("token_version = token_version + 1"));
        return AuthService.privateView(users.selectById(id));
    }
}
