package com.duilio.oj.controller;

import java.util.Map;
import com.duilio.oj.dto.Requests.ContestDraft;
import com.duilio.oj.security.CurrentUser;
import com.duilio.oj.service.ContestService;
import jakarta.validation.Valid;
import org.springframework.context.annotation.Profile;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/contests")
@Profile("!judge")
public class ContestController {
    private final ContestService contests;
    private final CurrentUser current;
    public ContestController(ContestService contests,CurrentUser current) { this.contests=contests; this.current=current; }
    @GetMapping Object list(@RequestParam(required=false) String visibility) { return contests.list(current.optional(),visibility); }
    @GetMapping("/{id}") Object detail(@PathVariable Long id) { contests.publishFinished(); return contests.view(contests.get(id,current.optional()),current.optional()); }
    @PostMapping Object create(@Valid @RequestBody ContestDraft input) { var actor=current.required(); return contests.view(contests.save(null,input,actor),actor); }
    @PutMapping("/{id}") Object update(@PathVariable Long id,@Valid @RequestBody ContestDraft input) { var actor=current.required(); return contests.view(contests.save(id,input,actor),actor); }
    @DeleteMapping("/{id}") Object delete(@PathVariable Long id) { contests.delete(id,current.required()); return Map.of("detail","Deleted"); }
    @GetMapping("/{id}/ranklist") Object rank(@PathVariable Long id) { return contests.ranklist(id,current.required()); }
}

