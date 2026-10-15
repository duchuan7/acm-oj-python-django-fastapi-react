"""Validate and import an exported Django snapshot into an EMPTY Java schema.
Dry-run is the default. --apply uses this checkout's Compose MySQL and one transaction.
All SQL identifiers are fixed; data values are represented as UTF-8 hex literals.
"""
import argparse, collections, datetime, json, re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLES = ["oj_user", "problem", "test_case", "contest", "contest_participant", "contest_problem", "submission",
          "case_result", "judge_outbox", "problem_proposal", "problem_solution", "blog_post", "contest_rank_snapshot"]

def value(item):
    if item is None:
        return "NULL"
    if isinstance(item, bool):
        return "1" if item else "0"
    if isinstance(item, (int, float)):
        return str(item)
    if isinstance(item, (dict, list)):
        item = json.dumps(item, ensure_ascii=False)
    return "CONVERT(X'" + str(item).encode("utf-8").hex() + "' USING utf8mb4)"

def instant(item):
    if item is None:
        return None
    return datetime.datetime.fromisoformat(item.replace("Z", "+00:00")).astimezone(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")

def insert(table, row):
    assert table in TABLES and all(k.replace("_", "").isalnum() for k in row)
    return "INSERT INTO " + table + " (" + ",".join(row) + ") VALUES (" + ",".join(value(v) for v in row.values()) + ");"

def convert(payload):
    if payload.get("format") != "duilio-oj-legacy-v1":
        raise ValueError("Unsupported snapshot format; use export_legacy.py")
    groups = collections.defaultdict(list)
    for obj in payload["objects"]:
        groups[obj["model"]].append(obj)
    result = []
    seen_emails = set()
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")
    for obj in groups["accounts.user"]:
        f = obj["fields"]
        password = f["password"]
        if not (password.startswith("pbkdf2_sha256$") or password.startswith("$2") or password.startswith("!")):
            raise ValueError("Unsupported password algorithm for user ID " + str(obj["pk"]) + "; reset it before export")
        email = f.get("email", "").strip().lower() or None
        if email and email in seen_emails:
            raise ValueError("Duplicate case-insensitive email")
        if email:
            seen_emails.add(email)
        result.append(insert("oj_user", dict(id=obj["pk"], username=f["username"], email=email, password=password,
            role="ADMIN" if f.get("is_staff") or f.get("is_superuser") else f["role"],
            school=f.get("school", ""), real_name=f.get("real_name", ""), active=f["is_active"], token_version=0,
            last_seen_at=instant(f.get("last_seen_at")), created_at=instant(f["date_joined"]))))
    for obj in groups["problems.problem"]:
        f = obj["fields"]
        row = {k: f[k] for k in ["title", "slug", "description", "input_description", "output_description", "samples",
                "time_limit_ms", "memory_limit_mb", "difficulty", "tags", "source", "is_public", "created_by"]}
        row.update(id=obj["pk"], created_at=instant(f["created_at"]), updated_at=instant(f["updated_at"]))
        result.append(insert("problem", row))
    for obj in groups["problems.testcase"]:
        f = obj["fields"]
        case = payload["testcase_files"].get(str(obj["pk"]))
        if case is None:
            raise ValueError("Missing testcase files for ID " + str(obj["pk"]))
        result.append(insert("test_case", dict(id=obj["pk"], problem_id=f["problem"], case_order=f["order"],
            input_text=case["input"], output_text=case["output"], score=f["score"], is_sample=f["is_sample"])))
    for obj in groups["contests.contest"]:
        f = obj["fields"]
        result.append(insert("contest", dict(id=obj["pk"], title=f["title"], description=f["description"], rule=f["rule"],
            start_at=instant(f["start_at"]), end_at=instant(f["end_at"]), is_public=f["is_public"],
            freeze_rank_minutes=f["freeze_rank_minutes"], created_by=f["created_by"], created_at=instant(f["created_at"]))))
        for uid in f.get("participants", []):
            result.append(insert("contest_participant", dict(contest_id=obj["pk"], user_id=uid)))
    for obj in groups["contests.contestproblem"]:
        f = obj["fields"]
        result.append(insert("contest_problem", dict(id=obj["pk"], contest_id=f["contest"], problem_id=f["problem"],
            alias=f["alias"], score=f["score"], problem_order=f["order"], created_for_contest=f["created_for_contest"])))
    for obj in groups["submissions.submission"]:
        f = obj["fields"]
        row = {k: f[k] for k in ["language", "code", "code_size", "verdict", "score", "max_time_ms", "max_memory_kb", "compile_message"]}
        if row["verdict"] == "JUDGING":
            row["verdict"] = "PENDING"
        row.update(id=obj["pk"], user_id=f["user"], problem_id=f["problem"], contest_id=f["contest"],
            submitted_at=instant(f["submitted_at"]), judged_at=instant(f["judged_at"]), judge_attempts=0)
        result.append(insert("submission", row))
        if row["verdict"] == "PENDING":
            result.append(insert("judge_outbox", dict(submission_id=obj["pk"], created_at=now)))
    for obj in groups["submissions.submissioncaseresult"]:
        f = obj["fields"]
        result.append(insert("case_result", dict(id=obj["pk"], submission_id=f["submission"], case_id=f["case"],
            status=f["status"], time_used=f["time_used"], memory_used=f["memory_used"], exit_code=f["exit_code"],
            stdout=f["stdout"], stderr=f["stderr"], score=f["score"],
            message=f.get("message", ""), created_at=instant(f.get("created_at")))))
    for obj in groups["problems.problemproposal"]:
        f = obj["fields"]
        data = {k: f[k] for k in ["title", "slug", "description", "input_description", "output_description", "samples",
                "time_limit_ms", "memory_limit_mb", "difficulty", "tags", "source"]}
        data.update(is_public=True, test_cases=[])
        if f.get("approved_problem"):
            cases = [o for o in groups["problems.testcase"] if o["fields"]["problem"] == f["approved_problem"]]
            for c in cases:
                content = payload["testcase_files"][str(c["pk"])]
                data["test_cases"].append(dict(order=c["fields"]["order"], input=content["input"], output=content["output"],
                    score=c["fields"]["score"], is_sample=c["fields"]["is_sample"]))
        result.append(insert("problem_proposal", dict(id=obj["pk"], author_id=f["author"], title=f["title"], problem_data=data,
            standard_language=f["standard_language"], standard_code=f["standard_code"], status=f["status"],
            review_message=f["review_message"], reviewed_by=f["reviewed_by"], approved_problem=f["approved_problem"],
            created_at=instant(f["created_at"]), reviewed_at=instant(f["reviewed_at"]))))
    for obj in groups["problems.problemsolution"]:
        f = obj["fields"]
        result.append(insert("problem_solution", dict(id=obj["pk"], problem_id=f["problem"], author_id=f["author"],
            title=f["title"], content=f["content"], status=f["status"], review_message=f["review_message"],
            reviewed_by=f["reviewed_by"], created_at=instant(f["created_at"]), reviewed_at=instant(f["reviewed_at"]),
            updated_at=instant(f["updated_at"]))))
    for obj in groups["blogs.blogpost"]:
        f = obj["fields"]
        result.append(insert("blog_post", dict(id=obj["pk"], author_id=f["author"], title=f["title"], content=f["content"],
            status=f["status"], created_at=instant(f["created_at"]), updated_at=instant(f["updated_at"]))))
    for obj in groups["contests.contestranksnapshot"]:
        f = obj["fields"]
        result.append(insert("contest_rank_snapshot", dict(id=obj["pk"], contest_id=f["contest"],
            generated_at=instant(f["generated_at"]), frozen=f["frozen"], payload=f["payload"])))
    return result

def mysql(sql, database=None):
    command = ["docker", "compose", "exec", "-T"]
    if database:
        if not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_]{0,63}", database):
            raise ValueError("Invalid database name")
        command += ["-e", "MYSQL_DATABASE=" + database]
    command += ["mysql", "sh", "-c",
               'MYSQL_PWD="$MYSQL_PASSWORD" exec mysql -u"$MYSQL_USER" "$MYSQL_DATABASE" --batch --skip-column-names --default-character-set=utf8mb4']
    result = subprocess.run(command, cwd=ROOT, input=sql, text=True, encoding="utf-8", capture_output=True)
    if result.returncode:
        raise RuntimeError("MySQL import failed and transaction was not committed: " + result.stderr[:1000])
    return result.stdout

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--apply", action="store_true", help="Write only into an empty target schema")
    parser.add_argument("--database", help="Explicit target database (default: Compose MYSQL_DATABASE)")
    args = parser.parse_args()
    payload = json.loads(args.snapshot.read_text(encoding="utf-8-sig"))
    statements = convert(payload)
    counts = collections.Counter(obj["model"] for obj in payload["objects"])
    print(json.dumps(dict(counts), indent=2))
    print(f"Validated {len(statements)} insert statements. IDs and password hashes are preserved.")
    if not args.apply:
        print("Dry-run only. No database changes.")
        return
    counts_sql = "SELECT " + "+".join("(SELECT COUNT(*) FROM " + table + ")" for table in TABLES) + ";"
    if mysql(counts_sql, args.database).strip() != "0":
        raise RuntimeError("Target schema is not empty. Use a separate empty database; no records were removed.")
    mysql("SET NAMES utf8mb4; SET time_zone='+00:00'; START TRANSACTION;\n" + "\n".join(statements) + "\nCOMMIT;", args.database)
    print("Import committed. Start API and judge, then compare source/target counts and sample login/verdicts.")

if __name__ == "__main__":
    main()
