"""Real Django -> export -> MySQL test, using disposable schemas only.
Requires Compose mysql and the original Django backend image. Never reads the user's legacy database.
"""
import argparse, importlib.util, json, re, secrets, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def execute(command, **kwargs):
    result = subprocess.run(command, cwd=ROOT, text=True, encoding="utf-8", capture_output=True, **kwargs)
    if result.returncode:
        raise RuntimeError("Command failed: " + result.stderr[-2000:])
    return result.stdout

def root_sql(sql):
    return execute(["docker", "compose", "exec", "-T", "mysql", "sh", "-c",
        'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --skip-column-names --default-character-set=utf8mb4'], input=sql)

def export_fixture(image):
    ident = execute(["docker", "run", "-d", "--rm", "--network=none",
        "--tmpfs", "/var/lib/postgresql/data:rw,size=256m",
        "-e", "POSTGRES_HOST_AUTH_METHOD=trust", "-e", "POSTGRES_DB=source",
        "-e", "POSTGRES_USER=legacy", "postgres:16-alpine"]).strip()
    assert re.fullmatch(r"[0-9a-f]{64}", ident)
    try:
        for _ in range(40):
            ready = subprocess.run(["docker", "exec", ident, "pg_isready", "-U", "legacy", "-d", "source"],
                capture_output=True)
            if ready.returncode == 0:
                break
            time.sleep(0.5)
        else:
            raise RuntimeError("Temporary PostgreSQL did not become ready")
        snapshot = execute(["docker", "run", "--rm", "--network=container:" + ident,
            "-e", "MIGRATION_TEST_POSTGRES=true",
            "--mount", "type=bind,source=" + str(ROOT / "migration") + ",target=/migration,readonly",
            image, "python", "/migration/tests/legacy_fixture.py"])
        count = execute(["docker", "exec", ident, "psql", "-U", "legacy", "-d", "source",
            "-tAc", "SELECT COUNT(*) FROM accounts_user;"]).strip()
        assert count == "2"
        print("PASS PostgreSQL consistent read-only snapshot", flush=True)
        return snapshot
    finally:
        execute(["docker", "rm", "-f", ident])

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy-image", default="acm-oj-python-django-fastapi-react-backend:latest")
    args = parser.parse_args()
    work = ROOT / ".runtime" / "roundtrip"
    work.mkdir(parents=True, exist_ok=True)
    snapshot = export_fixture(args.legacy_image)
    source = json.loads(snapshot)
    source_file = work / "legacy.json"
    source_file.write_text(snapshot, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("importer", ROOT / "migration" / "import_legacy.py")
    importer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(importer)
    names = ["oj_migration_check_" + secrets.token_hex(6) + suffix for suffix in ["", "_bad"]]
    ddl = "\n".join((ROOT / "backend" / "src" / "main" / "resources" / "db" / "migration" / name).read_text(encoding="utf-8")
        for name in ["V1__initial.sql", "V2__legacy_rank_snapshots.sql", "V3__case_result_history.sql"])
    try:
        for database in names:
            assert re.fullmatch(r"oj_migration_check_[0-9a-f]{12}(_bad)?", database)
            root_sql("CREATE DATABASE " + database + " CHARACTER SET utf8mb4; GRANT ALL ON " + database + ".* TO 'oj'@'%'; USE " + database + ";\n" + ddl)
        dry = execute([sys.executable, "migration/import_legacy.py", str(source_file), "--database", names[0]])
        assert "Dry-run only" in dry
        assert importer.mysql("SELECT COUNT(*) FROM oj_user;", names[0]).strip() == "0"
        print("PASS dry-run leaves target empty", flush=True)
        execute([sys.executable, "migration/import_legacy.py", str(source_file), "--database", names[0], "--apply"])
        checks = {
            "users and Django hashes": ("SELECT COUNT(*) FROM oj_user WHERE id IN (101,102) AND password LIKE 'pbkdf2_sha256$%';", "2"),
            "testcase contents": ("SELECT HEX(input_text),HEX(output_text) FROM test_case WHERE id=301;", "3120320A\t330A"),
            "submission history": ("SELECT COUNT(*) FROM submission WHERE id IN (501,502,503);", "3"),
            "pending and interrupted jobs requeued": ("SELECT COUNT(*) FROM judge_outbox;", "2"),
            "case results": ("SELECT status,score FROM case_result WHERE id=601;", "ACCEPTED\t100"),
            "private contest membership": ("SELECT COUNT(*) FROM contest_participant WHERE contest_id=401 AND user_id=102;", "1"),
            "proposal editorial blog and snapshot": ("SELECT (SELECT COUNT(*) FROM problem_proposal)+(SELECT COUNT(*) FROM problem_solution)+(SELECT COUNT(*) FROM blog_post)+(SELECT COUNT(*) FROM contest_rank_snapshot);", "5"),
        }
        for name, (sql, expected) in checks.items():
            assert importer.mysql(sql, names[0]).strip() == expected, name
            print("PASS " + name, flush=True)
        title = importer.mysql("SELECT title FROM problem WHERE id=201;", names[0]).strip()
        assert "迁移测试" in title and "' quotes" in title
        print("PASS Unicode and SQL-sensitive text preserved", flush=True)
        second = subprocess.run([sys.executable, "migration/import_legacy.py", str(source_file), "--database", names[0], "--apply"],
            cwd=ROOT, text=True, encoding="utf-8", capture_output=True)
        assert second.returncode != 0 and "not empty" in second.stderr
        assert importer.mysql("SELECT COUNT(*) FROM oj_user;", names[0]).strip() == "2"
        print("PASS repeated import refused without modifying records", flush=True)
        broken = json.loads(snapshot)
        next(obj for obj in broken["objects"] if obj["model"] == "blogs.blogpost")["fields"]["author"] = 99999
        broken_file = work / "invalid.json"
        broken_file.write_text(json.dumps(broken), encoding="utf-8")
        failed = subprocess.run([sys.executable, "migration/import_legacy.py", str(broken_file), "--database", names[1], "--apply"],
            cwd=ROOT, text=True, encoding="utf-8", capture_output=True)
        assert failed.returncode != 0
        assert importer.mysql("SELECT COUNT(*) FROM oj_user;", names[1]).strip() == "0"
        assert importer.mysql("SELECT COUNT(*) FROM submission;", names[1]).strip() == "0"
        print("PASS late import failure rolls back earlier inserts", flush=True)
        print("PASS: 12 migration checks", flush=True)
    finally:
        for database in names:
            if re.fullmatch(r"oj_migration_check_[0-9a-f]{12}(_bad)?", database):
                root_sql("DROP DATABASE IF EXISTS " + database + ";")

if __name__ == "__main__":
    main()
