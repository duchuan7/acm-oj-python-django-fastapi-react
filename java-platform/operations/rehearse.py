"""Rehearse real local legacy data in disposable Linux containers.

The original PostgreSQL must be STOPPED. Source volumes are only mounted read-only.
Private backups/snapshots never leave .runtime. No existing Java database is replaced.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "acceptance"))
from run import Acceptance, GOOD, HTTP, command


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


class Rehearsal(Acceptance):
    def __init__(self, args):
        super().__init__()
        self.args = args
        self.report["mode"] = "real local legacy data rehearsal"
        self.report["scope"] = "Local Docker Linux rehearsal only; no external server, DNS, production ingress or original database switch."
        self.private = self.work / "private"
        self.private.mkdir()
        self.source_db = json.loads(command(["docker", "inspect", args.legacy_db]))[0]
        self.source_api = json.loads(command(["docker", "inspect", args.legacy_backend]))[0]
        self.source_web = json.loads(command(["docker", "inspect", args.legacy_frontend]))[0]
        if self.source_db["State"]["Running"]:
            raise RuntimeError("Cold backup requires the original PostgreSQL to be stopped; no source service was changed.")
        self.pg = dict(item.split("=", 1) for item in self.source_db["Config"]["Env"] if "=" in item)
        self.old_env = dict(item.split("=", 1) for item in self.source_api["Config"]["Env"] if "=" in item)
        self.tokens.append(self.pg.get("POSTGRES_PASSWORD", "unused"))

    def cleanup(self):
        # The empty-target stage profiles out judge. Include it in final teardown
        # even if the run stopped before, or after, it was explicitly started.
        config = json.loads(self.compose_file.read_text())
        for service in config["services"].values():
            service.pop("profiles", None)
        self.compose_file.write_text(json.dumps(config, indent=2), encoding="utf-8")
        super().cleanup()
        for resource in ("container", "volume"):
            remaining = command(["docker", resource, "ls", "-aq" if resource == "container" else "-q",
                                 "--filter", "label=com.docker.compose.project=" + self.project])
            assert not remaining, "Owned Compose resources remain after cleanup"
        self.report["cleanup_verified_at"] = datetime.now(timezone.utc).isoformat()

    def cold_backup(self):
        volumes = {}
        for key, info, destination in [("postgres", self.source_db, "/var/lib/postgresql/data"), ("testcases", self.source_api, "/data/testcases")]:
            mount = next(m for m in info["Mounts"] if m["Destination"] == destination)
            if mount["Type"] != "volume":
                raise RuntimeError("Expected an explicit named legacy volume")
            volume = mount["Name"]
            volumes[key] = volume
            command(["docker", "run", "--rm", "--network", "none", "--mount", f"type=volume,src={volume},dst=/source,readonly",
                     "--mount", f"type=bind,src={self.private},dst=/backup", self.source_db["Image"], "sh", "-c",
                     f"test ! -e /backup/{key}.tgz && tar -czf /backup/{key}.tgz -C /source ."])
        self.report["source"] = {"database_container": self.args.legacy_db, "volumes": volumes, "database_was_stopped": True}
        self.report["backup_sha256"] = {key: digest(self.private / (key + ".tgz")) for key in volumes}
        self.check("cold PostgreSQL and testcase backups created through read-only source mounts")

    def clones(self):
        config = json.loads(self.compose_file.read_text())
        self.gateway_file = self.work / "gateway.conf"
        self.gateway_config("maintenance")
        pg_env = {key: self.pg[key] for key in ["POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"] if key in self.pg}
        config["services"].update({
            "legacy-db": {"image": self.source_db["Image"], "environment": pg_env, "mem_limit": "512m", "volumes": ["legacy_pg:/var/lib/postgresql/data"], "healthcheck": {"test": ["CMD-SHELL", 'pg_isready -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'], "interval": "2s", "timeout": "5s", "retries": 60}},
            "legacy-redis": {"image": "redis:7-alpine", "mem_limit": "96m"},
            "legacy-api": {"image": self.source_api["Image"], "mem_limit": "512m", "command": ["python", "manage.py", "runserver", "0.0.0.0:8000", "--noreload"],
                "environment": {**pg_env, "POSTGRES_HOST": "legacy-db", "POSTGRES_PORT": "5432", "REDIS_URL": "redis://legacy-redis:6379/0", "DJANGO_SECRET_KEY": self.secret, "DJANGO_ALLOWED_HOSTS": "legacy-api,localhost,127.0.0.1,testserver", "EMAIL_BACKEND": "django.core.mail.backends.locmem.EmailBackend"},
                "volumes": [f"{ROOT.parent / 'backend'}:/app:ro", "legacy_cases:/data/testcases:ro"], "depends_on": {"legacy-db": {"condition": "service_healthy"}}},
            "legacy-web": {"image": self.source_web["Image"], "mem_limit": "1536m", "environment": {"VITE_API_BASE": "/api", "NODE_OPTIONS": "--max-old-space-size=1024"}, "command": ["sh", "-c", "npm run build && npm run preview -- --host 0.0.0.0 --port 5173"], "volumes": [f"{ROOT.parent / 'frontend' / 'src'}:/app/src:ro"],
                "healthcheck": {"test": ["CMD", "node", "-e", "fetch('http://127.0.0.1:5173').then(r=>{if(!r.ok)process.exit(1)}).catch(()=>process.exit(1))"], "interval": "2s", "timeout": "5s", "retries": 90}},
            "gateway": {"image": config["services"]["web"]["image"], "mem_limit": "96m", "volumes": [f"{self.gateway_file}:/etc/nginx/conf.d/default.conf:ro"], "ports": [{"target": 80, "host_ip": "127.0.0.1", "published": "0"}]},
        })
        for key in ("legacy_pg", "legacy_cases"):
            config["volumes"][key] = {"name": self.project + "_" + key}
        self.compose_file.write_text(json.dumps(config, indent=2), encoding="utf-8")
        for key, archive in [("legacy_pg", "postgres"), ("legacy_cases", "testcases")]:
            name = self.project + "_" + key
            command(["docker", "volume", "create", "--label", "com.docker.compose.project=" + self.project, "--label", "com.docker.compose.volume=" + key, name])
            info = json.loads(command(["docker", "volume", "inspect", name]))[0]
            assert info["Labels"]["com.docker.compose.project"] == self.project
            command(["docker", "run", "--rm", "--network", "none", "--mount", f"type=volume,src={name},dst=/restore", "--mount", f"type=bind,src={self.private},dst=/backup,readonly",
                     self.source_db["Image"], "sh", "-c", f'test -z "$(ls -A /restore)" && tar -xzf /backup/{archive}.tgz -C /restore'])
        self.compose_file.write_text(json.dumps(config, indent=2), encoding="utf-8")
        self.compose("up", "-d", "--wait", "legacy-db", "legacy-redis", "legacy-api", "legacy-web", "gateway", timeout=180)
        self.gateway = "http://" + self.compose("port", "gateway", "80")
        for _ in range(80):
            try:
                self.compose("exec", "-T", "legacy-api", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/problems/').read()")
                break
            except Exception:
                time.sleep(.5)
        else:
            raise RuntimeError("Restored legacy API did not become ready")
        self.check("cold source backups restore into an independent working PostgreSQL and legacy API")

    def gateway_config(self, mode):
        if mode == "maintenance":
            locations = 'location / { add_header Retry-After 30 always; return 503 "Maintenance"; }'
        else:
            upstream = "legacy-web:5173" if mode == "legacy" else "web:80"
            api = "legacy-api:8000" if mode == "legacy" else "api:8088"
            locations = f'location /api/ {{ proxy_pass http://{api}; proxy_set_header Host localhost; }} location / {{ proxy_pass http://{upstream}; proxy_set_header Host localhost; }}'
        self.gateway_file.write_text("server { listen 80; " + locations + " }", encoding="utf-8")

    def switch(self, mode):
        self.gateway_config(mode)
        self.compose("exec", "-T", "gateway", "nginx", "-t")
        self.compose("exec", "-T", "gateway", "nginx", "-s", "reload")
        time.sleep(1)

    def export_import(self):
        snapshot = self.compose("exec", "-T", "legacy-api", "python", "-", data=(ROOT / "migration/export_legacy.py").read_text(encoding="utf-8"))
        path = self.private / "legacy.json"
        path.write_text(snapshot, encoding="utf-8")
        self.payload = json.loads(snapshot)
        self.report["legacy_models"] = dict(Counter(o["model"] for o in self.payload["objects"]))
        self.report["snapshot_sha256"] = digest(path)
        shutil.copytree(ROOT / "migration", self.work / "migration", ignore=shutil.ignore_patterns("__pycache__"))
        spec = importlib.util.spec_from_file_location("release_importer", self.work / "migration/import_legacy.py")
        self.importer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.importer)
        self.statements = self.importer.convert(self.payload)
        self.compose("stop", "api", "web")
        dry = command([sys.executable, "migration/import_legacy.py", str(path)], cwd=self.work)
        self.check("real legacy snapshot dry-run leaves target empty", "Dry-run only" in dry and self.sql("SELECT COUNT(*) FROM oj_user;") == "0")
        command([sys.executable, "migration/import_legacy.py", str(path), "--apply"], cwd=self.work)
        self.verify_rows()
        self.compose("start", "--wait", "api", "web", timeout=120)
        self.base = "http://" + self.compose("port", "api", "8088") + "/api"
        self.web = "http://" + self.compose("port", "web", "80")

    def verify_rows(self):
        json_columns = {tuple(line.split("\t")) for line in self.sql("SELECT TABLE_NAME,COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND DATA_TYPE='json';").splitlines()}
        counts, predicates = Counter(), []
        for statement in self.statements:
            match = re.fullmatch(r"INSERT INTO (\w+) \(([^)]+)\) VALUES \((.*)\);", statement)
            if not match:
                raise AssertionError("Unrecognized generated migration statement")
            table, columns, values = match.groups()
            columns, values = columns.split(","), values.split(",")
            assert len(columns) == len(values)
            conditions = []
            for column, value in zip(columns, values):
                if (table, column) in json_columns and value != "NULL":
                    value = "CAST(" + value + " AS JSON)"
                conditions.append(f"`{column}` <=> {value}")
            predicates.append(f"SELECT COUNT(*) FROM `{table}` WHERE " + " AND ".join(conditions) + ";")
            counts[table] += 1
        for offset in range(0, len(predicates), 100):
            actual = self.sql("\n".join(predicates[offset:offset+100])).splitlines()
            self.check(f"imported rows {offset+1}-{min(offset+100,len(predicates))} preserve all converted fields", all(n == "1" for n in actual) and len(actual) == len(predicates[offset:offset+100]))
        actual_counts = {t: int(self.sql(f"SELECT COUNT(*) FROM `{t}`;")) for t in self.importer.TABLES}
        self.check("all migrated model and relationship counts match the source conversion", actual_counts == {t: counts[t] for t in self.importer.TABLES})
        self.report["imported_tables"] = actual_counts

    def mysql_restore(self):
        result = subprocess.run(["docker", "compose", "-p", self.project, "-f", str(self.compose_file), "exec", "-T", "mysql", "sh", "-c", 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysqldump -uroot --single-transaction --skip-comments --no-tablespaces oj'], capture_output=True)
        if result.returncode:
            raise RuntimeError("Isolated MySQL backup failed")
        path = self.private / "java-mysql.sql"
        path.write_bytes(result.stdout)
        database = "oj_migration_check_" + self.project.rsplit("-", 1)[1] + "00"
        self.sql("CREATE DATABASE " + database + " CHARACTER SET utf8mb4;")
        self.sql(result.stdout.decode("utf-8"), database)
        checksums = {}
        for table in self.importer.TABLES:
            keys = self.sql(f"SELECT COLUMN_NAME FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='{table}' AND INDEX_NAME='PRIMARY' ORDER BY SEQ_IN_INDEX;").splitlines()
            sql = f"SELECT * FROM `{table}` ORDER BY " + ",".join("`" + key + "`" for key in keys) + ";"
            before, after = self.sql(sql), self.sql(sql, database)
            self.check("backup restore preserves complete rows in " + table, before == after)
            checksums[table] = hashlib.sha256(before.encode()).hexdigest()
        self.report["mysql_restore"] = {"dump_sha256": digest(path), "table_sha256": checksums}

    def authenticate(self):
        username = "release_" + self.project.rsplit("-", 1)[1]
        email = username + "@example.test"
        self.call("/auth/registration-code", "POST", {"email": email})
        mail = "http://" + self.compose("port", "mailpit", "8025")
        for _ in range(40):
            with HTTP.open(mail + "/api/v1/messages") as response:
                messages = json.load(response)["messages"]
            match = next((m for m in messages if any(p["Address"] == email for p in m["To"])), None)
            if match:
                with HTTP.open(mail + "/api/v1/message/" + match["ID"]) as response:
                    code = re.search(r"code is (\d{6})", json.load(response)["Text"]).group(1)
                break
            time.sleep(.2)
        else:
            raise RuntimeError("Local verification message was not delivered")
        session = self.call("/auth/register", "POST", {"username": username, "email": email, "password": self.secret, "code": code})
        self.tokens.append(session["token"])
        ident = session["user"]["id"]
        # Test identity only; never alter the role/password of an imported source account.
        self.sql(f"UPDATE oj_user SET role='ADMIN',token_version=token_version+1 WHERE id={ident};")
        self.admin = self.login(username)
        self.check("isolated imported deployment supports fresh registration through test email")
        candidate = next((o for o in self.payload["objects"] if o["model"] == "accounts.user" and o["fields"]["username"] == self.old_env.get("DEMO_ADMIN_USERNAME", "admin")), None)
        password = self.old_env.get("DEMO_ADMIN_PASSWORD")
        if self.args.legacy_login_file:
            credential = json.loads(self.args.legacy_login_file.read_text(encoding="utf-8-sig"))
            candidate = next((o for o in self.payload["objects"] if o["model"] == "accounts.user" and o["fields"]["username"] == credential.get("username")), None)
            password = credential.get("password")
            if not candidate or not isinstance(password, str) or not password:
                raise ValueError("Local login file needs an imported username and a nonempty password; values suppressed")
        if candidate and password:
            self.tokens.append(password)
            try:
                account = self.call("/auth/login", "POST", {"username": candidate["fields"]["username"], "password": password})
                self.tokens.append(account["token"])
                self.check("configured original admin password logs into imported Java account", account["user"]["id"] == candidate["pk"])
                self.report["legacy_password_login"] = "passed using existing local configuration; credential omitted"
            except AssertionError:
                if self.args.legacy_login_file:
                    raise
                self.report["legacy_password_login"] = "configured demo credential does not match the real account; hashes preserved exactly, generated legacy-login regression covers compatibility"
        else:
            self.report["legacy_password_login"] = "no plaintext legacy credential in existing local configuration; hashes preserved exactly, generated legacy-login regression covers compatibility"

    def historical_ranks(self):
        source = """import os,json,django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
django.setup()
from django.utils import timezone
from apps.contests.models import Contest
from apps.contests.serializers import build_ranklist
print(json.dumps({str(c.pk):build_ranklist(c) for c in Contest.objects.filter(end_at__lt=timezone.now())}))
"""
        expected = json.loads(self.compose("exec", "-T", "legacy-api", "python", "-", data=source))
        for ident, rows in expected.items():
            actual = self.call("/contests/" + ident + "/ranklist", token=self.admin["token"])["results"]
            keys = ["rank", "user_id", "username", "solved", "score", "total_time_ms"]
            self.check("real historical contest " + ident + " retains original standings", rows == [{k: row[k] for k in keys} for row in actual])
        self.report["historical_ranklists_compared"] = len(expected)

    def judge_and_stability(self):
        config = json.loads(self.compose_file.read_text())
        config["services"]["api"]["command"] = ["--oj.jobs.enabled=true"]
        config["services"]["api"]["environment"].pop("OJ_JOBS_ENABLED", None)
        self.compose_file.write_text(json.dumps(config, indent=2), encoding="utf-8")
        self.compose("up", "-d", "--wait", "api", "judge", "web", timeout=150)
        self.base = "http://" + self.compose("port", "api", "8088") + "/api"
        self.web = "http://" + self.compose("port", "web", "80")
        self.call("/problems", base=self.web + "/api")
        self.check("web proxy still reaches API after API container replacement")
        problem = self.problem(0)
        problem.update(title="Release four-language check", slug="release-" + self.project.rsplit("-", 1)[1])
        problem = self.call("/problems", "POST", problem, self.admin["token"])
        records = [self.submit(self.admin, problem["id"], code, language=language) for language, code in GOOD.items()]
        self.wait_results(records)
        started = time.monotonic()
        results = []
        def read(index):
            begin = time.monotonic()
            try:
                self.call(["/problems", "/contests", "/users/leaderboard"][index % 3])
                return (time.monotonic()-begin)*1000, True
            except Exception:
                return (time.monotonic()-begin)*1000, False
        with ThreadPoolExecutor(max_workers=10) as pool:
            while time.monotonic()-started < self.args.duration:
                batch = time.monotonic()
                results.extend(pool.map(read, range(10)))
                time.sleep(max(0, 1-(time.monotonic()-batch)))
        times = sorted(r[0] for r in results)
        p95 = times[int(len(times)*.95)-1]
        self.report["stability"] = {"duration_seconds": round(time.monotonic()-started, 2), "requests": len(results), "concurrent_clients": 10, "errors": sum(not r[1] for r in results), "p95_ms": round(p95, 2), "scope": "short local soak; not multi-day production evidence"}
        self.check("configured local soak has no errors and P95 below 2000ms", all(r[1] for r in results) and p95 < 2000)

    def cutover(self):
        def browser(mode):
            command(["node", "acceptance/cutover.mjs", self.project, self.gateway, mode, str(self.private)], cwd=ROOT/"frontend", timeout=120)
            self.check(mode + " browser uses the rehearsal gateway without JavaScript errors")
        self.switch("legacy")
        old = self.call("/problems/", base=self.gateway + "/api")
        self.check("isolated entrypoint initially serves the restored legacy API", isinstance(old, list) or "results" in old)
        browser("legacy")
        self.switch("maintenance")
        request = urllib.request.Request(self.gateway + "/api/problems")
        try:
            HTTP.open(request, timeout=10)
            raise AssertionError("Maintenance did not reject requests")
        except urllib.error.HTTPError as error:
            self.check("maintenance blocks entrypoint requests with Retry-After", error.code == 503 and error.headers.get("Retry-After") == "30")
        self.switch("java")
        current = self.call("/problems", base=self.gateway + "/api")
        self.check("same isolated entrypoint switches to the imported Java API", isinstance(current, dict) and "count" in current)
        browser("java")
        self.load()
        self.switch("maintenance")
        self.switch("legacy")
        again = self.call("/problems/", base=self.gateway + "/api")
        self.check("rollback returns the same entrypoint to unchanged legacy problem data", old == again)
        browser("rollback")
        self.switch("java")
        self.check("source PostgreSQL remains stopped after the rehearsal", not json.loads(command(["docker", "inspect", self.args.legacy_db]))[0]["State"]["Running"])
        self.report["cutover"] = {"scope": "isolated loopback gateway only", "sequence": ["legacy", "maintenance", "java", "maintenance", "legacy rollback", "java"], "original_entrypoints_changed": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy-db", default="acmoj-db")
    parser.add_argument("--legacy-backend", default="acmoj-backend")
    parser.add_argument("--legacy-frontend", default="acmoj-frontend")
    parser.add_argument("--duration", type=int, default=300, help="Short soak seconds (default 300; not a multi-day stability claim)")
    parser.add_argument("--legacy-login-file", type=Path, help="Optional private JSON containing username/password; never pass passwords in command arguments")
    args = parser.parse_args()
    if args.duration < 1:
        parser.error("duration must be positive")
    test = Rehearsal(args)
    success = False
    try:
        for name, action in [("source cold backups", test.cold_backup), ("isolated Linux target", lambda: test.setup(empty=True)), ("restore old deployment", test.clones), ("real data migration", test.export_import), ("test login", test.authenticate), ("historical standings", test.historical_ranks), ("MySQL restore drill", test.mysql_restore), ("four-language judging and short soak", test.judge_and_stability), ("entrypoint switch and rollback", test.cutover)]:
            test.stage(name, action)
        success = True
    except Exception as error:
        # Detailed diagnostics may contain private source data: retain only in ignored directory.
        import traceback
        (test.private / "failure.log").write_text(traceback.format_exc(), encoding="utf-8")
        test.report["failure"] = {"type": type(error).__name__, "message": "Private diagnostics saved locally"}
        try:
            (test.private / "services.log").write_text(test.compose("logs", "--no-color"), encoding="utf-8")
        except Exception:
            pass
    finally:
        if test.compose_file.exists():
            try:
                test.cleanup()
                test.report["cleanup"] = "owned test resources removed; private backups retained"
            except Exception:
                test.report["cleanup"] = "failed; inspect private diagnostics"
                success = False
        test.report["success"] = success
        test.report["finished_at"] = datetime.now(timezone.utc).isoformat()
        test.save()
    print("REPORT " + str(test.work / "report.json"), flush=True)
    print("PASS" if success else "FAILED", flush=True)
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
