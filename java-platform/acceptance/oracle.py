"""Independent expected-result calculator for acceptance fixtures.

No application code or observed verdict/score is imported: fixtures supply those.
The server supplies only record IDs and submission timestamps.
"""
from collections import defaultdict
from datetime import datetime


def instant(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def rank(rule, attempts, start, weights, cutoff=None):
    groups = defaultdict(lambda: defaultdict(list))
    start = instant(start)
    for item in sorted(attempts, key=lambda r: (instant(r["submitted_at"]), r["id"])):
        if cutoff and instant(item["submitted_at"]) >= instant(cutoff):
            continue
        groups[item["user_id"]][item["problem_id"]].append(item)
    results = []
    for user, problems in groups.items():
        solved = score = penalty = 0
        for problem, records in problems.items():
            if rule == "ACM":
                accepted = next((r for r in records if r["expected_verdict"] == "ACCEPTED"), None)
                if accepted:
                    solved += 1
                    penalty += int((instant(accepted["submitted_at"]) - start).total_seconds() // 60)
                    penalty += 20 * sum(r["expected_verdict"] == "WRONG_ANSWER" for r in records[:records.index(accepted)])
            else:
                best = max(records, key=lambda r: r["expected_score"])
                points = best["expected_score"] * weights[problem] // 100
                score += points
                if points:
                    solved += 1
                    penalty += int((instant(best["submitted_at"]) - start).total_seconds() // 60)
        results.append({"user_id":user,"solved":solved,"score":score,"penalty_minutes":penalty})
    key = "score" if rule == "IOI" else "solved"
    results.sort(key=lambda r: (-r[key], r["penalty_minutes"], r["user_id"]))
    return [{"rank":i + 1, **row} for i, row in enumerate(results)]


def normalize(rows):
    return [{key:row[key] for key in ("rank","user_id","solved","score","penalty_minutes")} for row in rows]
