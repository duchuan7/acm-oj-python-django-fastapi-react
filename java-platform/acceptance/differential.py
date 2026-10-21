"""Replay selected legacy contracts against the imported Java API, in test resources only."""
import json
import secrets
import shutil
import subprocess
import sys
import time


def replay(test, command, root):
    migration = test.work / "migration"
    if not migration.exists():
        shutil.copytree(root/"migration",migration,ignore=shutil.ignore_patterns("__pycache__"))
    legacy_image="acm-oj-python-django-fastapi-react-backend:latest"
    database="oj_migration_check_"+secrets.token_hex(6)
    postgres=command(["docker","run","-d","--rm","--network=none",
        "--label=duilio.oj.namespace="+test.project,"--tmpfs","/var/lib/postgresql/data:rw,size=256m",
        "-e","POSTGRES_HOST_AUTH_METHOD=trust","-e","POSTGRES_DB=source","-e","POSTGRES_USER=legacy","postgres:16-alpine"])
    try:
        for _ in range(60):
            ready=subprocess.run(["docker","exec",postgres,"pg_isready","-U","legacy","-d","source"],capture_output=True)
            if ready.returncode==0: break
            time.sleep(.5)
        else: raise AssertionError("Disposable legacy PostgreSQL failed to start")
        snapshot=command(["docker","run","--rm","--network=container:"+postgres,
            "--label=duilio.oj.namespace="+test.project,"-e","MIGRATION_TEST_POSTGRES=true",
            "--mount","type=bind,source="+str(migration)+",target=/migration,readonly",
            legacy_image,"python","/migration/tests/legacy_fixture.py"])
        old=json.loads(command(["docker","run","--rm","--network=container:"+postgres,
            "--label=duilio.oj.namespace="+test.project,
            "--mount","type=bind,source="+str(root/"acceptance")+",target=/acceptance,readonly",
            legacy_image,"python","/acceptance/legacy_replay.py"]))
        test.sql("CREATE DATABASE "+database+" CHARACTER SET utf8mb4; GRANT ALL ON "+database+".* TO 'oj'@'%';")
        config=json.loads(test.compose_file.read_text())
        api=json.loads(json.dumps(config["services"]["api"]))
        api["environment"]["DB_URL"]="jdbc:mysql://mysql:3306/"+database+"?connectionTimeZone=UTC"
        api["command"]=["--oj.jobs.enabled=false","--oj.bootstrap-admin=false","--oj.seed-demo=false"]
        config["services"]["replay"]=api
        test.compose_file.write_text(json.dumps(config,indent=2),encoding="utf-8")
        test.compose("up","-d","--no-deps","--wait","replay",timeout=120)
        # Let Flyway create the real schema/history before importing the empty target.
        snapshot_path = test.work/"legacy-replay.json"
        snapshot_path.write_text(snapshot,encoding="utf-8")
        command([sys.executable,"migration/import_legacy.py",str(snapshot_path),"--database",database,"--apply"],cwd=test.work)
        base="http://"+test.compose("port","replay","8088")+"/api"
        session=test.call("/auth/login","POST",{"username":"legacy_member","password":"legacy-member-password"},base=base)
        token=session["token"]
        test.tokens.append(token)
        test.check("Django password authenticates through Java API and upgrades to BCrypt",test.sql("SELECT password FROM oj_user WHERE id=102;",database).startswith("$2"))
        def new(path): return test.call(path,token=token,base=base)
        def fields(value,keys): return {key:value[key] for key in keys}
        def rows(value): return value if isinstance(value,list) else value["results"]
        def contents(value,keys): return sorted([fields(r,keys) for r in rows(value)],key=lambda r:r["id"])
        problem_keys=["id","title","slug","description","input_description","output_description","samples","time_limit_ms","memory_limit_mb","difficulty","tags","source","is_public"]
        test.check("legacy/Java problem fields, Unicode and samples agree",fields(old["problem"],problem_keys)==fields(new("/problems/201"),problem_keys))
        test.check("legacy/Java public profile statistics agree",old["profile"]["stats"]==new("/users/102/profile")["stats"])
        for key,path,keys in [
            ("blogs","/blogs",["id","title","content","status"]),
            ("editorials","/problem-solutions",["id","title","content","status"]),
            ("proposals","/problem-proposals",["id","title","status","standard_language","standard_code"]),
        ]:
            test.check("legacy/Java "+key+" business fields agree",contents(old[key],keys)==contents(new(path),keys))
        submission=new("/submissions/501")
        submission_keys=["id","problem","contest","language","verdict","score"]
        test.check("legacy/Java accepted submission business fields agree",fields(old["submission"],submission_keys)==fields(submission,submission_keys))
        exported_code=next(obj["fields"]["code"] for obj in json.loads(snapshot)["objects"] if obj["model"]=="submissions.submission" and obj["pk"]==501)
        test.check("Java owner source view preserves exported legacy code",submission["code"]==exported_code)
        case_keys=["status","time_used","memory_used","score"]
        test.check("legacy/Java per-case historical verdicts agree",[fields(c,case_keys) for c in old["submission"]["case_results"]]==[fields(c,case_keys) for c in submission["case_results"]])
        test.check("interrupted legacy JUDGING is deliberately imported as PENDING",new("/submissions/503")["verdict"]=="PENDING")
        for key, ident in [("acm_rank",401),("ioi_rank",404)]:
            actual=new(f"/contests/{ident}/ranklist")["results"]
            keys=["rank","user_id","username","solved","score","total_time_ms"]
            test.check("imported "+key+" preserves original Django standings",[fields(r,keys) for r in old[key]]==[fields(r,keys) for r in actual])
        test.report["differential"]={"source":"generated legacy PostgreSQL fixture", "old_transport":"Django APIClient in original backend image", "new_transport":"real HTTP to separately imported Java API", "compared":"problem/profile/blog/editorial/proposal/submission/case business fields", "expected_differences":["DRF Token versus JWT","field aliases and date formats normalized","interrupted judging requeued","legacy code is write-only in normal API; Java owner source checked against export"]}
        test.report["differential"]["legacy_image"] = command(["docker","image","inspect",legacy_image,"--format","{{.Id}}"])
    finally:
        # Exact container ID is created in this function; never a user database.
        command(["docker","rm","-f",postgres])
