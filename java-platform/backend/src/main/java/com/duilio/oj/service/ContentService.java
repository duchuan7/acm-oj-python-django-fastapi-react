package com.duilio.oj.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.UpdateWrapper;
import com.duilio.oj.common.*;
import com.duilio.oj.dto.Requests.*;
import com.duilio.oj.mapper.*;
import com.duilio.oj.model.*;
import com.duilio.oj.security.CurrentUser;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.*;

@Service
public class ContentService {
    private final ProblemProposalMapper proposals;
    private final ProblemSolutionMapper solutions;
    private final BlogPostMapper blogs;
    private final UserMapper users;
    private final ProblemService problems;
    private final Json json;

    public ContentService(
            ProblemProposalMapper proposals,
            ProblemSolutionMapper solutions,
            BlogPostMapper blogs,
            UserMapper users,
            ProblemService problems,
            Json json) {
        this.proposals = proposals;
        this.solutions = solutions;
        this.blogs = blogs;
        this.users = users;
        this.problems = problems;
        this.json = json;
    }

    private void editable(Long author, User actor, boolean adminOnly) {
        ApiException.require(
                actor != null
                        && (actor.id.equals(author)
                                || (adminOnly
                                        ? CurrentUser.admin(actor)
                                        : CurrentUser.staff(actor))),
                403,
                "You can only modify your own content");
    }

    public Object proposalList(User actor, String status) {
        var q = new QueryWrapper<ProblemProposal>().orderByDesc("id");
        if (!CurrentUser.staff(actor)) q.eq("author_id", actor.id);
        if (status != null) q.eq("status", status);
        return proposals.selectList(q.last("LIMIT 200")).stream().map(this::proposalView).toList();
    }

    public ProblemProposal proposal(Long id, User actor) {
        return proposal(id, actor, false);
    }

    private ProblemProposal proposal(Long id, User actor, boolean lock) {
        var q = new QueryWrapper<ProblemProposal>().eq("id", id);
        if (lock) q.last("FOR UPDATE");
        var p = proposals.selectOne(q);
        ApiException.require(
                p != null && (CurrentUser.staff(actor) || p.authorId.equals(actor.id)),
                404,
                "Proposal not found");
        return p;
    }

    public Object proposalView(ProblemProposal p) {
        var v = json.view(p);
        v.put("problem", json.read(p.problemData, ProblemDraft.class));
        v.remove("problem_data");
        v.put("author_username", users.selectById(p.authorId).username);
        return v;
    }

    @Transactional
    public Object saveProposal(Long id, Proposal input, User actor) {
        var p = id == null ? new ProblemProposal() : proposal(id, actor, true);
        if (id != null) {
            editable(p.authorId, actor, true);
            ApiException.require(
                    CurrentUser.admin(actor) || "PENDING".equals(p.status),
                    403,
                    "Only pending proposals can be edited");
        } else {
            p.authorId = actor.id;
            p.status = "PENDING";
            p.reviewMessage = "";
            p.createdAt = Instant.now();
        }
        p.title = input.problem().title();
        p.problemData = json.write(input.problem());
        p.standardLanguage = input.standardLanguage();
        p.standardCode = input.standardCode();
        if (id == null) proposals.insert(p);
        else proposals.updateById(p);
        return proposalView(p);
    }

    @Transactional
    public Object reviewProposal(Long id, Review input, boolean approve, User actor) {
        var p =
                proposals.selectOne(
                        new QueryWrapper<ProblemProposal>().eq("id", id).last("FOR UPDATE"));
        ApiException.require(p != null, 404, "Proposal not found");
        ApiException.require(
                "PENDING".equals(p.status), 409, "Only pending proposals can be reviewed");
        if (approve)
            p.approvedProblem =
                    problems.save(
                                    null,
                                    json.read(p.problemData, ProblemDraft.class),
                                    users.selectById(p.authorId),
                                    true)
                            .id;
        p.status = approve ? "APPROVED" : "REJECTED";
        p.reviewMessage = Objects.requireNonNullElse(input.reviewMessage(), "");
        p.reviewedBy = actor.id;
        p.reviewedAt = Instant.now();
        proposals.updateById(p);
        return proposalView(p);
    }

    public void deleteProposal(Long id, User actor) {
        var p = proposal(id, actor);
        editable(p.authorId, actor, true);
        proposals.deleteById(id);
    }

    public Object solutionList(User actor, Long problem, String status) {
        var q = new QueryWrapper<ProblemSolution>().orderByDesc("id");
        if (problem != null) q.eq("problem_id", problem);
        if (status != null) q.eq("status", status);
        if (!CurrentUser.staff(actor))
            q.and(
                    w -> {
                        w.eq("status", "APPROVED");
                        if (actor != null) w.or().eq("author_id", actor.id);
                    });
        return solutions.selectList(q.last("LIMIT 200")).stream()
                .filter(p -> problems.get(p.problemId).isPublic || CurrentUser.staff(actor))
                .map(this::solutionView)
                .toList();
    }

    public ProblemSolution solution(Long id, User actor) {
        return solution(id, actor, false);
    }

    private ProblemSolution solution(Long id, User actor, boolean lock) {
        var q = new QueryWrapper<ProblemSolution>().eq("id", id);
        if (lock) q.last("FOR UPDATE");
        var p = solutions.selectOne(q);
        ApiException.require(
                p != null
                        && (CurrentUser.staff(actor)
                                || ("APPROVED".equals(p.status)
                                        && problems.get(p.problemId).isPublic)
                                || (actor != null && p.authorId.equals(actor.id))),
                404,
                "Editorial not found");
        return p;
    }

    public Object solutionView(ProblemSolution p) {
        var v = json.view(p);
        v.put("problem", p.problemId);
        v.put("author_username", users.selectById(p.authorId).username);
        v.put("problem_title", problems.get(p.problemId).title);
        return v;
    }

    @Transactional
    public Object saveSolution(Long id, Editorial input, User actor) {
        var problem = problems.get(input.problem());
        ApiException.require(
                problem.isPublic || CurrentUser.staff(actor), 403, "Problem unavailable");
        var p = id == null ? new ProblemSolution() : solution(id, actor, true);
        if (id != null) {
            editable(p.authorId, actor, true);
            ApiException.require(
                    p.problemId.equals(input.problem()), 400, "Cannot change editorial problem");
        } else {
            p.authorId = actor.id;
            p.createdAt = Instant.now();
        }
        p.problemId = input.problem();
        p.title = input.title();
        p.content = input.content();
        p.updatedAt = Instant.now();
        p.status = "PENDING";
        p.reviewMessage = "";
        if (id == null) solutions.insert(p);
        else {
            solutions.updateById(p);
            solutions.update(
                    new UpdateWrapper<ProblemSolution>()
                            .eq("id", id)
                            .set("reviewed_by", null)
                            .set("reviewed_at", null));
            p.reviewedBy = null;
            p.reviewedAt = null;
        }
        return solutionView(p);
    }

    @Transactional
    public Object reviewSolution(Long id, Review input, boolean approve, User actor) {
        var p =
                solutions.selectOne(
                        new QueryWrapper<ProblemSolution>().eq("id", id).last("FOR UPDATE"));
        ApiException.require(p != null, 404, "Editorial not found");
        ApiException.require(
                "PENDING".equals(p.status), 409, "Only pending editorials can be reviewed");
        p.status = approve ? "APPROVED" : "REJECTED";
        p.reviewMessage = Objects.requireNonNullElse(input.reviewMessage(), "");
        p.reviewedBy = actor.id;
        p.reviewedAt = Instant.now();
        solutions.updateById(p);
        return solutionView(p);
    }

    public void deleteSolution(Long id, User actor) {
        var p = solution(id, actor);
        editable(p.authorId, actor, true);
        solutions.deleteById(id);
    }

    public Object blogList(User actor, Long author) {
        var q = new QueryWrapper<BlogPost>().orderByDesc("id");
        if (author != null) q.eq("author_id", author);
        if (!CurrentUser.staff(actor))
            q.and(
                    w -> {
                        w.eq("status", "PUBLISHED");
                        if (actor != null) w.or().eq("author_id", actor.id);
                    });
        return blogs.selectList(q.last("LIMIT 200")).stream().map(this::blogView).toList();
    }

    public BlogPost blog(Long id, User actor) {
        var p = blogs.selectById(id);
        ApiException.require(
                p != null
                        && ("PUBLISHED".equals(p.status)
                                || CurrentUser.staff(actor)
                                || (actor != null && p.authorId.equals(actor.id))),
                404,
                "Blog not found");
        return p;
    }

    public Object blogView(BlogPost p) {
        var v = json.view(p);
        v.put("author_username", users.selectById(p.authorId).username);
        return v;
    }

    public Object saveBlog(Long id, Blog input, User actor) {
        var p = id == null ? new BlogPost() : blog(id, actor);
        if (id != null) editable(p.authorId, actor, false);
        else {
            p.authorId = actor.id;
            p.createdAt = Instant.now();
        }
        p.title = input.title();
        p.content = input.content();
        p.status = input.status();
        p.updatedAt = Instant.now();
        if (id == null) blogs.insert(p);
        else blogs.updateById(p);
        return blogView(p);
    }

    public void deleteBlog(Long id, User actor) {
        var p = blog(id, actor);
        editable(p.authorId, actor, false);
        blogs.deleteById(id);
    }
}
