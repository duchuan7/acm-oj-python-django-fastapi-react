package com.duilio.oj.controller;

import java.util.Map;
import com.duilio.oj.common.ApiException;
import com.duilio.oj.dto.Requests.*;
import com.duilio.oj.security.CurrentUser;
import com.duilio.oj.service.ContentService;
import jakarta.validation.Valid;
import org.springframework.context.annotation.Profile;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api")
@Profile("!judge")
public class ContentController {
    private final ContentService content;
    private final CurrentUser current;
    public ContentController(ContentService content,CurrentUser current) { this.content=content; this.current=current; }
    @GetMapping Object root() { return Map.of("name","duilio OJ","version","java21","modules",java.util.List.of("auth","problems","submissions","contests","problem-proposals","problem-solutions","blogs","users")); }
    @GetMapping("/problem-proposals") Object proposals(@RequestParam(required=false) String status) { return content.proposalList(current.required(),status); }
    @GetMapping("/problem-proposals/{id}") Object proposal(@PathVariable Long id) { return content.proposalView(content.proposal(id,current.required())); }
    @PostMapping("/problem-proposals") Object propose(@Valid @RequestBody Proposal input) { return content.saveProposal(null,input,current.required()); }
    @PutMapping("/problem-proposals/{id}") Object updateProposal(@PathVariable Long id,@Valid @RequestBody Proposal input) { return content.saveProposal(id,input,current.required()); }
    @DeleteMapping("/problem-proposals/{id}") Object deleteProposal(@PathVariable Long id) { content.deleteProposal(id,current.required()); return Map.of("detail","Deleted"); }
    @PostMapping("/problem-proposals/{id}/{action:approve|reject}") Object reviewProposal(@PathVariable Long id,@PathVariable String action,@Valid @RequestBody Review input) {
        return content.reviewProposal(id,input,action.equals("approve"),current.requireAdmin());
    }
    @GetMapping("/problem-solutions") Object solutions(@RequestParam(required=false) Long problem,@RequestParam(required=false) String status) { return content.solutionList(current.optional(),problem,status); }
    @GetMapping("/problem-solutions/{id}") Object solution(@PathVariable Long id) { return content.solutionView(content.solution(id,current.optional())); }
    @PostMapping("/problem-solutions") Object createSolution(@Valid @RequestBody Editorial input) { return content.saveSolution(null,input,current.required()); }
    @PutMapping("/problem-solutions/{id}") Object updateSolution(@PathVariable Long id,@Valid @RequestBody Editorial input) { return content.saveSolution(id,input,current.required()); }
    @DeleteMapping("/problem-solutions/{id}") Object deleteSolution(@PathVariable Long id) { content.deleteSolution(id,current.required()); return Map.of("detail","Deleted"); }
    @PostMapping("/problem-solutions/{id}/{action:approve|reject}") Object reviewSolution(@PathVariable Long id,@PathVariable String action,@Valid @RequestBody Review input) {
        return content.reviewSolution(id,input,action.equals("approve"),current.requireAdmin());
    }
    @GetMapping("/blogs") Object blogs(@RequestParam(required=false) Long author) { return content.blogList(current.optional(),author); }
    @GetMapping("/blogs/{id}") Object blog(@PathVariable Long id) { return content.blogView(content.blog(id,current.optional())); }
    @PostMapping("/blogs") Object createBlog(@Valid @RequestBody Blog input) { return content.saveBlog(null,input,current.required()); }
    @PutMapping("/blogs/{id}") Object updateBlog(@PathVariable Long id,@Valid @RequestBody Blog input) { return content.saveBlog(id,input,current.required()); }
    @DeleteMapping("/blogs/{id}") Object deleteBlog(@PathVariable Long id) { content.deleteBlog(id,current.required()); return Map.of("detail","Deleted"); }
}

