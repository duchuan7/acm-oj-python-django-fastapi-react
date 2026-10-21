"""Compare the real problem-list HTTP endpoint against a pre-optimization image.

All fixtures, SQL logging and cleanup belong to one disposable Compose project.
Never reads .env or connects to the normal OJ databases. Requires Python 3.12+.
"""
import argparse
import base64
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import hmac
import io
import json
import math
from pathlib import Path
import re
import secrets
import statistics
import subprocess
import sys
import tarfile
import time
import traceback
from urllib.parse import urlencode
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "acceptance"))
from run import command, HTTP

BASELINE_REF = "5ba1b3b2c849dff5534fca4eafaddf15cddfa5dd"


def summary(samples):
    ordered = sorted(samples)
    return {"requests": len(samples), "p50_ms": round(statistics.median(ordered), 2),
            "p95_ms": round(ordered[math.ceil(len(ordered) * .95) - 1], 2)}


class Benchmark:
    def __init__(self, args):
        self.args = args
        self.project = "oj-sqlbench-" + secrets.token_hex(5)
        self.work = ROOT / ".runtime" / "benchmarks" / self.project
        self.work.mkdir(parents=True)
        self.compose_file = self.work / "compose.json"
        self.secret = secrets.token_hex(24)
        self.jwt_key = secrets.token_hex(32)
        self.report = {"project": self.project, "started_at": datetime.now(timezone.utc).isoformat(),
                       "source_commit": command(["git", "rev-parse", "HEAD"]), "checks": [],
                       "source_diff_sha256": hashlib.sha256(command(["git", "diff", "--binary"]).encode()).hexdigest(),
                       "scope": "Synthetic data, warm caches, local Docker Linux. Not production traffic or a public capacity claim."}

    def compose(self, *args, **kwargs):
        assert re.fullmatch(r"oj-sqlbench-[a-f0-9]{10}", self.project)
        assert self.compose_file.parent.resolve().is_relative_to((ROOT / ".runtime/benchmarks").resolve())
        return command(["docker", "compose", "-p", self.project, "-f", str(self.compose_file), *args], **kwargs)

    def sql(self, query):
        return self.compose("exec", "-T", "mysql", "sh", "-c",
                            'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot -N -B --default-character-set=utf8mb4 oj', data=query)

    def check(self, name, condition):
        self.report["checks"].append({"name": name, "passed": bool(condition)})
        print(("PASS " if condition else "FAIL ") + name, flush=True)
        if not condition:
            raise AssertionError(name)

    def images(self):
        before, candidate = self.args.baseline_image, self.args.candidate_image
        if self.args.build_images:
            ref = command(["git", "rev-parse", self.args.baseline_ref + "^{commit}"])
            assert re.fullmatch(r"[0-9a-f]{40}", ref)
            archive = subprocess.run(["git", "archive", ref, "java-platform/backend"], cwd=ROOT.parent,
                                     capture_output=True, check=True).stdout
            context = self.work / "baseline-source"
            with tarfile.open(fileobj=io.BytesIO(archive)) as files:
                files.extractall(context, filter="data")
            before, candidate = self.project + "-before", self.project + "-candidate"
            print("BUILD baseline and candidate images (including JUnit)", flush=True)
            command(["docker", "build", "--target", "runtime", "-t", before,
                     str(context / "java-platform/backend")], timeout=1200)
            command(["docker", "build", "--target", "runtime", "-t", candidate, str(ROOT / "backend")], timeout=1200)
            self.report["baseline_source_commit"] = ref
        if not before or not candidate:
            raise ValueError("Use --build-images, or provide both --baseline-image and --candidate-image")
        image_id = lambda image: command(["docker", "image", "inspect", image, "--format", "{{.Id}}"])
        self.before = image_id(before)
        candidate = image_id(candidate)
        command(["docker", "tag", self.before, self.project + "-before-runtime"])
        command(["docker", "tag", candidate, self.project + "-candidate-runtime"])
        # Reuse the exact baseline runtime layers. Only /app/app.jar changes, even
        # when a mutable JRE base tag received updates between the two builds.
        context = self.work / "matched-runtime"
        context.mkdir()
        (context / "Dockerfile").write_text(
            f"FROM {self.project}-candidate-runtime AS candidate\nFROM {self.project}-before-runtime\nCOPY --from=candidate /app/app.jar /app/app.jar\n", encoding="utf-8")
        command(["docker", "build", "-t", self.project + "-after", str(context)], timeout=120)
        self.after = image_id(self.project + "-after")
        versions = []
        for image in (self.before, self.after):
            result = subprocess.run(["docker", "run", "--rm", "--network", "none", "--entrypoint", "java", image, "-version"],
                                    capture_output=True, text=True, check=True)
            versions.append(result.stdout + result.stderr)
        self.check("baseline and optimized API use identical JRE versions and runtime layers", versions[0] == versions[1])
        self.report["images"] = {"baseline": self.before, "candidate_artifact": candidate, "optimized_matched_runtime": self.after}
        self.report["java_runtime"] = versions[0].strip()
        info = json.loads(command(["docker", "info", "--format", "{{json .}} "]))
        self.report["docker"] = {key: info[key] for key in ("ServerVersion", "OSType", "NCPU", "MemTotal")}

    def setup(self):
        health = lambda text: {"test": ["CMD-SHELL", text], "interval": "2s", "timeout": "5s", "retries": 90}
        config = {"services": {
            "mysql": {"image": "mysql:8.4", "mem_limit": "1g", "cpus": 2, "environment": {
                "MYSQL_DATABASE": "oj", "MYSQL_USER": "oj", "MYSQL_PASSWORD": self.secret, "MYSQL_ROOT_PASSWORD": self.secret},
                "volumes": ["data:/var/lib/mysql"], "healthcheck": health("MYSQL_PWD=$$MYSQL_PASSWORD mysql --protocol=TCP -h 127.0.0.1 -u$$MYSQL_USER oj -Nse 'SELECT 1'")},
            "redis": {"image": "redis:7-alpine", "mem_limit": "96m", "healthcheck": health("redis-cli ping")},
            "rabbit": {"image": "rabbitmq:4.3.6-management", "mem_limit": "512m", "environment": {
                "RABBITMQ_DEFAULT_USER": "oj", "RABBITMQ_DEFAULT_PASS": self.secret}, "healthcheck": health("rabbitmq-diagnostics -q ping")}},
            "volumes": {"data": {}}}
        for name, image in (("before", self.before), ("after", self.after)):
            config["services"][name] = {"image": image, "mem_limit": "768m", "cpus": 1,
                "command": ["--oj.jobs.enabled=false"], "environment": {
                    "DB_URL": "jdbc:mysql://mysql:3306/oj?connectionTimeZone=UTC", "DB_USER": "bench_" + name,
                    "DB_PASSWORD": self.secret, "REDIS_HOST": "redis", "REDIS_PORT": "6379",
                    "RABBIT_HOST": "rabbit", "RABBIT_PORT": "5672", "RABBIT_PASSWORD": self.secret,
                    "JWT_SECRET": self.jwt_key, "BOOTSTRAP_ADMIN": "false", "SEED_DEMO": "false", "SMTP_HOST": "mailpit"},
                "ports": [{"target": 8088, "host_ip": "127.0.0.1", "published": "0"}],
                "healthcheck": health("curl -fsS http://localhost:8088/actuator/health")}
        self.compose_file.write_text(json.dumps(config, indent=2), encoding="utf-8")
        self.compose("up", "-d", "--wait", "mysql", "redis", "rabbit", timeout=240)
        for name in ("before", "after"):
            self.sql(f"CREATE USER 'bench_{name}'@'%' IDENTIFIED BY '{self.secret}'; GRANT ALL ON oj.* TO 'bench_{name}'@'%';")
            self.compose("up", "-d", "--wait", name, timeout=150)
        self.addresses = {name: "http://" + self.compose("port", name, "8088") for name in ("before", "after")}
        for service in config["services"]:
            ident = self.compose("ps", "-q", service)
            labels = json.loads(command(["docker", "inspect", ident]))[0]["Config"]["Labels"]
            self.check("isolated resource ownership: " + service, labels["com.docker.compose.project"] == self.project)
        self.report["limits"] = {"api_each": {"cpus": 1, "memory_mib": 768}, "mysql": {"cpus": 2, "memory_mib": 1024}}

    def fixtures(self):
        sql = """
        CREATE TABLE bench_n(n INT PRIMARY KEY);
        INSERT INTO bench_n SELECT a.n+10*b.n+100*c.n+1000*d.n FROM
        (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) a
        CROSS JOIN (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) b
        CROSS JOIN (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) c
        CROSS JOIN (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) d;
        INSERT INTO oj_user(id,username,password,role,created_at) VALUES
        (1,'synthetic_admin','unused','ADMIN','2026-01-01'),(2,'synthetic_member','unused','MEMBER','2026-01-01');
        INSERT INTO problem(id,title,slug,description,input_description,output_description,samples,time_limit_ms,memory_limit_mb,difficulty,tags,source,is_public,created_by,created_at,updated_at)
        SELECT n+1,CONCAT('Synthetic problem ',n+1),CONCAT('sql-bench-',n+1),'Synthetic statement 中文','Two integers','One integer','[]',1000,256,
        800+MOD(n+1,20)*100,JSON_ARRAY('bench',CONCAT('group',MOD(n+1,5)),'tag space'),'Synthetic SQL benchmark',MOD(n+1,10)<>0,1,'2026-01-01','2026-01-01' FROM bench_n;
        INSERT INTO submission(id,user_id,problem_id,language,code,code_size,verdict,score,compile_message,submitted_at)
        SELECT n+1,2,p,'CPP','synthetic',9,
        CASE WHEN MOD(p,13)=0 THEN 'WRONG_ANSWER' WHEN MOD(n,3)=0 THEN 'ACCEPTED' ELSE ELT(1+MOD(n,4),'WRONG_ANSWER','COMPILE_ERROR','PENDING','JUDGING') END,
        CASE WHEN MOD(p,13)<>0 AND MOD(n,3)=0 THEN 100 ELSE 0 END,'','2026-01-01'
        FROM (SELECT n,CASE WHEN MOD(p,17)=0 THEN p+1 ELSE p END p FROM
          (SELECT n,CASE WHEN MOD(n,4)=0 THEN 1+MOD(n DIV 4,30) ELSE 101+MOD(n,9900) END p FROM
            (SELECT a.n+10000*b.n n FROM bench_n a CROSS JOIN bench_n b WHERE b.n<10) numbers) distribution) fixture;
        DROP TABLE bench_n;
        ANALYZE TABLE problem,submission;
        """
        self.sql(sql)
        self.counts, self.accepted = Counter(), Counter()
        for n in range(100000):
            p = 1 + (n // 4) % 30 if n % 4 == 0 else 101 + n % 9900
            p += int(p % 17 == 0)
            self.counts[p] += 1
            self.accepted[p] += int(p % 13 != 0 and n % 3 == 0)
        self.check("fixture is exactly 10000 synthetic problems and 100000 synthetic submissions",
                   self.sql("SELECT COUNT(*) FROM problem; SELECT COUNT(*) FROM submission;").splitlines() == ["10000", "100000"])
        self.report["dataset"] = {"problems": 10000, "submissions": 100000, "public_problems": 9000,
            "distribution": "25% of submissions target first 30 problems; multiples of 17 have zero submissions; multiples of 13 have no AC",
            "origin": "deterministic generated fixtures; not real users or real judging activity", "fixture_sql_sha256": hashlib.sha256(sql.encode()).hexdigest()}
        self.dataset_digest = self.sql("SELECT COUNT(*),SUM(id),SUM(score),SUM(problem_id) FROM submission;")

    def token(self, ident):
        encode = lambda value: base64.urlsafe_b64encode(json.dumps(value, separators=(",", ":")).encode()).rstrip(b"=")
        header, payload = encode({"alg": "HS256", "typ": "JWT"}), encode({"sub": str(ident), "version": 0,
            "iss": "duilio-oj", "iat": int(time.time()), "exp": int(time.time()) + 3600})
        message = header + b"." + payload
        return (message + b"." + base64.urlsafe_b64encode(hmac.digest(self.jwt_key.encode(), message, "sha256")).rstrip(b"=")).decode()

    def request(self, name, params=None, actor=None):
        url = self.addresses[name] + "/api/problems" + ("?" + urlencode(params) if params else "")
        headers = {"Authorization": "Bearer " + self.token(actor)} if actor else {}
        with HTTP.open(urllib.request.Request(url, headers=headers), timeout=60) as response:
            return json.load(response)

    def correctness(self):
        scenarios = [("public first page", {}, None), ("second page", {"page": 2}, None),
            ("later page", {"page": 101}, None), ("last partial page", {"difficulty_min": 2700, "page": 17}, None),
            ("empty page", {"page": 9999}, None), ("negative page clamps to first", {"page": -3}, None),
            ("title search", {"search": "problem 170"}, None), ("source search", {"search": "SQL benchmark"}, None),
            ("difficulty bounds", {"difficulty_min": 1200, "difficulty_max": 1500}, None),
            ("tag filter", {"tag": "group2"}, None), ("tag containing whitespace", {"tag": "tag space"}, None),
            ("bound SQL input", {"search": "synthetic%' OR 1=1 --"}, None),
            ("member visibility", {}, 2), ("admin private problems", {}, 1)]
        for label, params, actor in scenarios:
            before, after = [self.request(name, params, actor) for name in ("before", "after")]
            self.check("identical full JSON: " + label, before == after)
            for row in after["results"]:
                ident = row["id"]
                assert row["submission_count"] == self.counts[ident]
                assert row.get("accepted_count") == (self.accepted[ident] if self.counts[ident] else None)
                assert "test_cases" not in row
                assert actor == 1 or row["is_public"]
        self.check("submission statistics match independent Python fixture oracle", True)
        self.check("public/member and administrator visibility counts are preserved",
                   self.request("after")["count"] == 9000 and self.request("after", actor=1)["count"] == 10000)

    def query_log(self):
        records, plans = {}, {}
        self.report["sql_queries"] = records
        for name in ("before", "after"):
            for page in (1, 9999):
                self.sql("SET GLOBAL general_log='OFF'; SET GLOBAL log_output='TABLE'; TRUNCATE TABLE mysql.general_log; SET GLOBAL general_log='ON';")
                try:
                    self.request(name, {"page": page})
                finally:
                    self.sql("SET GLOBAL general_log='OFF';")
                # argument is a binary/blob column on MySQL. LOWER(argument) does
                # not reliably lowercase it; filter decoded statements in Python.
                logged = self.sql("SELECT argument FROM mysql.general_log WHERE command_type IN ('Query','Execute') AND user_host LIKE 'bench_" + name + "[bench_" + name + "]%' ORDER BY event_time;").splitlines()
                decoded = [query.replace("\\n", "\n").replace("\\t", "\t") for query in logged]
                queries = [query for query in decoded if re.match(r"\s*SELECT\b", query, re.I)
                           and not re.fullmatch(r"\s*SELECT\s+1\s*;?\s*", query, re.I)]
                (self.work / f"sql-{name}-{page}.json").write_text(json.dumps(decoded, indent=2), encoding="utf-8")
                counts = Counter()
                for query in queries:
                    lowered = query.lower()
                    if "from submission" in lowered:
                        counts["statistics"] += 1
                        plans.setdefault(name, query)
                    elif "from contest" in lowered:
                        counts["contest_publication_check"] += 1
                    elif "count(" in lowered:
                        counts["page_count"] += 1
                    else:
                        counts["page_rows"] += 1
                records[f"{name}_page_{page}"] = {"select_count": len(queries), "by_purpose": dict(counts)}
                expected = (33 if name == "before" else 4) if page == 1 else 3
                self.check(f"MySQL general log: {name} page {page} executes {len(queries)} SELECTs (expected {expected})", len(queries) == expected)
        self.report["sql_queries"] = records
        self.report["explain_analyze"] = {name: self.sql("EXPLAIN ANALYZE " + query) for name, query in plans.items()}
        self.report["statistics_sql_examples"] = plans
        self.check("general SQL logging is disabled before timing", self.sql("SELECT @@general_log;") == "0")

    def timing(self):
        for _ in range(self.args.warmup):
            for name in ("before", "after"):
                self.request(name)
        workloads = {}
        for clients in (1, 8):
            collected = {name: [] for name in ("before", "after")}
            rounds = []
            for index in range(self.args.rounds):
                order = ("before", "after") if index % 2 == 0 else ("after", "before")
                for name in order:
                    def read(_):
                        start = time.perf_counter()
                        data = self.request(name)
                        assert data["count"] == 9000 and len(data["results"]) == 30
                        return (time.perf_counter() - start) * 1000
                    start = time.perf_counter()
                    with ThreadPoolExecutor(max_workers=clients) as pool:
                        samples = list(pool.map(read, range(self.args.requests)))
                    elapsed = time.perf_counter() - start
                    collected[name].extend(samples)
                    rounds.append({"round": index + 1, "variant": name, **summary(samples),
                                   "elapsed_seconds": round(elapsed, 3), "requests_per_second": round(len(samples) / elapsed, 2)})
                    print(f"TIMING {clients} clients round {index + 1} {name}: {summary(samples)}", flush=True)
            workloads[str(clients)] = {"clients": clients, "rounds": rounds,
                                       **{name: summary(values) for name, values in collected.items()}, "errors": 0}
        self.report["http_timing"] = workloads
        self.report["timing_method"] = {"warmup_requests_per_variant": self.args.warmup,
            "rounds": self.args.rounds, "requests_per_variant_per_round": self.args.requests,
            "order": "alternating AB then BA", "path": "/api/problems?page=1, anonymous",
            "caches": "warmed JVM and MySQL; list endpoint does not use Redis cache", "sql_logging_during_timing": False}
        self.check("synthetic submissions remain unchanged throughout the read benchmark",
                   self.dataset_digest == self.sql("SELECT COUNT(*),SUM(id),SUM(score),SUM(problem_id) FROM submission;"))

    def cleanup(self):
        if not self.compose_file.exists():
            return
        self.compose("down", "--volumes", "--remove-orphans", timeout=120)
        for resource in ("container", "volume"):
            remaining = command(["docker", resource, "ls", "-aq" if resource == "container" else "-q",
                                 "--filter", "label=com.docker.compose.project=" + self.project])
            assert not remaining, "Owned benchmark resources remain"
        self.report["cleanup"] = "only owned containers and synthetic database volume removed; normal OJ untouched"

    def save(self):
        text = json.dumps(self.report, ensure_ascii=False, indent=2)
        for secret in (self.secret, self.jwt_key):
            text = text.replace(secret, "[REDACTED]")
        (self.work / "report.json").write_text(text + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-image")
    parser.add_argument("--candidate-image")
    parser.add_argument("--build-images", action="store_true")
    parser.add_argument("--baseline-ref", default=BASELINE_REF)
    parser.add_argument("--warmup", type=int, default=30)
    parser.add_argument("--rounds", type=int, default=4)
    parser.add_argument("--requests", type=int, default=80)
    args = parser.parse_args()
    if min(args.warmup, args.rounds, args.requests) < 1:
        parser.error("warmup, rounds and requests must be positive")
    test = Benchmark(args)
    success = False
    try:
        for name in ("images", "setup", "fixtures", "correctness", "query_log", "timing"):
            print("STAGE " + name, flush=True)
            getattr(test, name)()
            test.save()
        success = True
    except Exception as error:
        (test.work / "failure.log").write_text(traceback.format_exc(), encoding="utf-8")
        test.report["failure"] = {"type": type(error).__name__, "message": "See ignored local diagnostics"}
    finally:
        try:
            test.cleanup()
        except Exception:
            (test.work / "cleanup-failure.log").write_text(traceback.format_exc(), encoding="utf-8")
            test.report["cleanup"] = "failed; see ignored local diagnostics"
            success = False
        test.report["success"] = success
        test.report["finished_at"] = datetime.now(timezone.utc).isoformat()
        test.save()
    print("REPORT " + str(test.work / "report.json"), flush=True)
    print("PASS" if success else "FAILED", flush=True)
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
