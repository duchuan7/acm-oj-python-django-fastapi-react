package com.duilio.oj.controller;

import java.util.Map;
import com.duilio.oj.dto.Requests.ProblemDraft;
import com.duilio.oj.security.CurrentUser;
import com.duilio.oj.service.*;
import jakarta.validation.Valid;
import org.springframework.context.annotation.Profile;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/problems")
@Profile("!judge")
public class ProblemController {
    private final ProblemService problems;
    private final ContestService contests;
    private final CurrentUser current;
    public ProblemController(ProblemService problems,ContestService contests,CurrentUser current) { this.problems=problems; this.contests=contests; this.current=current; }
    @GetMapping Object list(@RequestParam(required=false) String search,@RequestParam(required=false) String tag,
        @RequestParam(name="difficulty_min",required=false) Integer min,@RequestParam(name="difficulty_max",required=false) Integer max,
        @RequestParam(defaultValue="1") int page) { contests.publishFinished(); return problems.list(search,tag,min,max,page,current.optional()); }
    @GetMapping("/{id}") Object detail(@PathVariable Long id,@RequestParam(required=false) Long contest) {
        var actor=current.optional(); return problems.cachedView(contests.readableProblem(id,contest,actor),CurrentUser.staff(actor));
    }
    @PostMapping Object create(@Valid @RequestBody ProblemDraft input) { return problems.view(problems.save(null,input,current.requireStaff(),null),true); }
    @PutMapping("/{id}") Object update(@PathVariable Long id,@Valid @RequestBody ProblemDraft input) { return problems.view(problems.save(id,input,current.requireStaff(),null),true); }
    @DeleteMapping("/{id}") Object delete(@PathVariable Long id) { current.requireStaff(); problems.delete(id); return Map.of("detail","Deleted"); }
}

