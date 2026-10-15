"""Run isolated multi-user acceptance. Never reads the development .env.

Run from java-platform: python acceptance/run.py
Needs Docker, Node/npm, installed frontend dependencies and the built OJ images.
All database changes, fault injection and cleanup target a newly generated project.
"""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import statistics
import subprocess
import sys
import time
import traceback
import urllib.error
import urllib.request

from oracle import instant, normalize, rank

ROOT = Path(__file__).resolve().parents[1]
HTTP = urllib.request.build_opener(urllib.request.ProxyHandler({}))
TERMINAL = {"ACCEPTED","WRONG_ANSWER","TIME_LIMIT_EXCEEDED","MEMORY_LIMIT_EXCEEDED","COMPILE_ERROR","RUNTIME_ERROR","OUTPUT_LIMIT_EXCEEDED","SYSTEM_ERROR"}
GOOD = {
    "C": '#include <stdio.h>\nint main(){long long a,b;scanf("%lld%lld",&a,&b);printf("%lld\\n",a+b);}',
    "CPP": '#include <iostream>\nint main(){long long a,b;std::cin>>a>>b;std::cout<<a+b<<"\\n";}',
    "JAVA": 'import java.util.*; public class Main {public static void main(String[] x){Scanner s=new Scanner(System.in);System.out.println(s.nextLong()+s.nextLong());}}',
    "PYTHON": 'a,b=map(int,input().split());print(a+b)',
}
EXPRESSIONS = ["a+b","a-b","a*b","max(a,b)","min(a,b)","abs(a-b)"]


def command(args, cwd=ROOT, data=None, timeout=240):
    result = subprocess.run(args, cwd=cwd, input=data, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=timeout)
    if result.returncode:
        raise RuntimeError("Command failed: " + " ".join(args[:4]) + "\n" + result.stdout[-1500:] + result.stderr[-1500:])
    return result.stdout.strip()


class Acceptance:
    def __init__(self):
        self.project = "oj-acceptance-" + secrets.token_hex(5)
        self.work = ROOT / ".runtime" / "acceptance" / self.project
        self.work.mkdir(parents=True)
        self.compose_file = self.work / "compose.yml"
        self.secret = secrets.token_hex(24)
        self.report = {"project":self.project,"started_at":datetime.now(timezone.utc).isoformat(),
                       "application_commit":command(["git","rev-parse","HEAD"]),"stages":[],"checks":[],
                       "scope":"Synthetic users and isolated Compose project; not production cutover or a security proof."}
        self.tokens = []
        self.report["source_diff_sha256"] = hashlib.sha256(command(["git","diff","--binary"]).encode()).hexdigest()
        self.records = []
        self.last_submit = {}
        self.checks = self.report["checks"]
        self.state = {"password":self.secret,"project":self.project}

    def compose(self, *args, **kwargs):
        assert re.fullmatch(r"oj-acceptance-[a-f0-9]{10}", self.project)
        assert self.compose_file.parent.resolve().is_relative_to((ROOT / ".runtime/acceptance").resolve())
        return command(["docker","compose","-p",self.project,"-f",str(self.compose_file),*args], **kwargs)

    def sql(self, text, database="oj"):
        assert re.fullmatch(r"oj(?:_migration_check_[a-f0-9]{12}(?:_bad)?)?", database)
        return self.compose("exec","-T","mysql","sh","-c",
                            'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot -N -B --default-character-set=utf8mb4 ' + database, data=text)

    def check(self, label, condition=True, **details):
        self.checks.append({"name":label,"passed":bool(condition),**details})
        print(("PASS " if condition else "FAIL ") + label, flush=True)
        if not condition:
            raise AssertionError(label)

    def call(self, path, method="GET", body=None, token=None, expected=200, base=None):
        request = urllib.request.Request((base or self.base) + path,
            data=None if body is None else json.dumps(body).encode(), method=method,
            headers={"Content-Type":"application/json", **({"Authorization":"Bearer " + token} if token else {})})
        try:
            with HTTP.open(request, timeout=60) as response:
                status, data = response.status, json.load(response)
        except urllib.error.HTTPError as error:
            status, data = error.code, json.loads(error.read() or b"{}")
        if status != expected:
            raise AssertionError(f"{method} {path}: expected {expected}, received {status}")
        return data

    def login(self, name):
        data = self.call("/auth/login","POST",{"username":name,"password":self.secret})
        self.tokens.append(data["token"])
        return {"id":data["user"]["id"],"username":name,"token":data["token"]}

    def stage(self, name, action):
        print("STAGE " + name, flush=True)
        entry = {"name":name,"status":"running"}
        self.report["stages"].append(entry)
        start = time.monotonic()
        try:
            action()
            entry["status"] = "passed"
        except Exception as error:
            entry["status"] = "failed"
            entry["error"] = str(error)
            raise
        finally:
            entry["seconds"] = round(time.monotonic() - start, 2)
            self.save()

    def save(self):
        self.report["attempts"] = [{k:v for k,v in row.items() if k not in {"user_token","accepted_at_monotonic"}} for row in self.records]
        text = json.dumps(self.report,ensure_ascii=False,indent=2)
        for secret in [self.secret,*self.tokens]:
            text = text.replace(secret,"[REDACTED]")
        (self.work / "report.json").write_text(text,encoding="utf-8")

    def setup(self):
        images = {}
        for service, image in {"api":"duilio-oj-java-api:latest","judge":"duilio-oj-java-judge:latest", "web":"duilio-oj-java-web:latest"}.items():
            images[service] = command(["docker","image","inspect",image,"--format","{{.Id}}"])
        self.report["images"] = images
        database = {"DB_URL":"jdbc:mysql://mysql:3306/oj?connectionTimeZone=UTC", "DB_PASSWORD":self.secret,
                    "REDIS_HOST":"redis","REDIS_PORT":"6379","RABBIT_HOST":"rabbit","RABBIT_PORT":"5672","RABBIT_PASSWORD":self.secret}
        api = {**database,"JWT_SECRET":secrets.token_hex(32),"ADMIN_USERNAME":"accept_admin","ADMIN_PASSWORD":self.secret,
               "SEED_DEMO":"false","SMTP_HOST":"mailpit","SMTP_PORT":"1025","SMTP_AUTH":"false","SMTP_SSL":"false", "MAIL_FROM":"acceptance@example.test"}
        health = lambda cmd: {"test":["CMD-SHELL",cmd],"interval":"2s","timeout":"5s","retries":90}
        ports = lambda port: [{"target":port,"host_ip":"127.0.0.1","published":"0"}]
        config = {"name":self.project,"services":{
            "mysql":{"image":"mysql:8.4","environment":{"MYSQL_DATABASE":"oj","MYSQL_USER":"oj","MYSQL_PASSWORD":self.secret,"MYSQL_ROOT_PASSWORD":self.secret},"volumes":["mysql_data:/var/lib/mysql"],"command":["--character-set-server=utf8mb4","--collation-server=utf8mb4_0900_ai_ci"],"mem_limit":"768m","healthcheck":health('MYSQL_PWD=$$MYSQL_ROOT_PASSWORD mysqladmin ping -h localhost -u root --silent')},
            "redis":{"image":"redis:7-alpine","mem_limit":"128m","healthcheck":health("redis-cli ping")},
            "rabbit":{"image":"rabbitmq:4.3.6-management","environment":{"RABBITMQ_DEFAULT_USER":"oj","RABBITMQ_DEFAULT_PASS":self.secret},"mem_limit":"512m","ports":ports(15672),"healthcheck":health("rabbitmq-diagnostics -q ping")},
            "mailpit":{"image":"axllent/mailpit:v1.29","mem_limit":"96m","ports":ports(8025)},
            "api":{"image":images["api"],"environment":api,"mem_limit":"768m","ports":ports(8088),"depends_on":{key:{"condition":"service_healthy"} for key in ("mysql","redis","rabbit")},"healthcheck":health("curl -fsS http://localhost:8088/actuator/health")},
            "judge":{"image":images["judge"],"environment":{**database,"OJ_MODE":"judge","SPRING_PROFILES_ACTIVE":"judge","SEED_DEMO":"false","BOOTSTRAP_ADMIN":"false","JUDGE_NAMESPACE":self.project},"mem_limit":"512m","volumes":["/var/run/docker.sock:/var/run/docker.sock"],"depends_on":{"api":{"condition":"service_healthy"}}},
            "web":{"image":images["web"],"ports":ports(80),"mem_limit":"96m","depends_on":{"api":{"condition":"service_healthy"}}},
        },"volumes":{"mysql_data":{}}}
        self.compose_file.write_text(json.dumps(config,indent=2),encoding="utf-8")
        # Only synthetic secrets are written here; legacy migration helpers use this private copy.
        (self.work / ".env").write_text("MYSQL_ROOT_PASSWORD="+self.secret+"\nDB_PASSWORD="+self.secret+"\n",encoding="utf-8")
        self.compose("up","-d","--wait",timeout=240)
        def address(service, port):
            binding = self.compose("port",service,str(port)).splitlines()[0]
            assert re.fullmatch(r"127\.0\.0\.1:\d+",binding)
            return "http://" + binding
        self.base = address("api",8088) + "/api"
        self.web = address("web",80)
        self.mail = address("mailpit",8025)
        self.rabbit = address("rabbit",15672)
        self.state.update(base=self.base,web=self.web,mail=self.mail,work=str(self.work))
        self.admin = self.login("accept_admin")
        self.check("isolated environment uses only local test mail", self.compose("exec","-T","api","printenv","SMTP_HOST")=="mailpit")
        for service in ("mysql","redis","rabbit","api","judge","web"):
            ident = self.compose("ps","-q",service)
            info = json.loads(command(["docker","inspect",ident]))[0]
            self.check("owned isolated container: " + service, info["Config"]["Labels"]["com.docker.compose.project"]==self.project)

    def problem(self, index, public=True):
        expression = EXPRESSIONS[index % len(EXPRESSIONS)]
        values = [(17,4),(-9,2)]
        cases = [{"order":i+1,"input":f"{a} {b}\n","output":str(eval(expression,{"__builtins__":{},"max":max,"min":min,"abs":abs},{"a":a,"b":b}))+"\n","score":50,"is_sample":i==0} for i,(a,b) in enumerate(values)]
        return {"title":f"Acceptance {index+1}","slug":"acceptance-"+str(index),"description":"Synthetic arithmetic problem. 中文题面。", "input_description":"Two integers", "output_description":expression,"samples":[{"input":cases[0]["input"],"output":cases[0]["output"]}], "time_limit_ms":1000,"memory_limit_mb":256,"difficulty":800+index*100,"tags":["acceptance"],"source":"Synthetic machine acceptance","is_public":public,"test_cases":cases}

    def fixtures(self):
        for role, names in [("COACH",["coach_1","coach_2"]),("MEMBER",[f"student_{i:02}" for i in range(19)])]:
            for name in names:
                self.sql("INSERT INTO oj_user(username,email,password,role,active,created_at) SELECT '"+name+"','"+name+"@example.test',password,'"+role+"',true,NOW(6) FROM oj_user WHERE username='accept_admin';")
        self.coaches = [self.login("coach_1"),self.login("coach_2")]
        self.students = [self.login(f"student_{i:02}") for i in range(19)]
        self.problems = [self.call("/problems","POST",self.problem(i),self.coaches[0]["token"]) for i in range(6)]
        self.hidden = self.call("/problems","POST",self.problem(6,False),self.coaches[0]["token"])
        memory_problem = {**self.problem(7),"title":"Acceptance memory boundary","time_limit_ms":5000,"memory_limit_mb":64}
        self.memory_problem = self.call("/problems","POST",memory_problem,self.coaches[0]["token"])
        self.state.update(admin=self.admin,coaches=self.coaches,students=self.students,problems=self.problems,hidden=self.hidden,
                          registration={"username":"student_19","email":"student_19@example.test"})
        self.check("seeded 1 administrator, 2 coaches, 19 students; final student registers in browser")

    def browser(self):
        state_path = self.work / "browser-state.json"
        state_path.write_text(json.dumps(self.state),encoding="utf-8")
        env = {**os.environ,"OJ_ACCEPTANCE_STATE":str(state_path)}
        npm = "npm.cmd" if os.name=="nt" else "npm"
        result = subprocess.run([npm,"run","test:acceptance"],cwd=ROOT/"frontend",env=env,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=240)
        (self.work/"browser.log").write_text(result.stdout+result.stderr,encoding="utf-8")
        self.check("multi-role browser journeys, real registration and network recovery",result.returncode==0)
        self.students.append(self.login("student_19"))

    def create_contest(self, rule, start, end, private=False):
        body = {"title":"Acceptance "+rule+(" private" if private else ""),"description":"Machine simulation", "rule":rule,"start_at":start,"end_at":end,"is_public":not private,"freeze_rank_minutes":1,"participants":[s["id"] for s in self.students[:10]],"contest_problems":[{"problem":p["id"],"new_problem":None,"alias":chr(65+i),"score":(40 if i==0 else 60) if rule=="IOI" else 100,"order":i+1} for i,p in enumerate(self.problems[:2] if rule=="IOI" else self.problems)]}
        return self.call("/contests","POST",body,(self.coaches[0] if private else self.admin)["token"])

    def submit(self, user, problem, code, verdict="ACCEPTED", score=100, language="PYTHON", contest=None):
        delay = 1.1 - (time.monotonic() - self.last_submit.get(user["id"],0))
        if delay > 0: time.sleep(delay)
        start = time.monotonic()
        data = self.call("/submissions","POST",{"problem":problem,"contest":contest,"language":language,"code":code},user["token"])
        self.last_submit[user["id"]] = time.monotonic()
        record = {"id":data["id"],"user_id":user["id"],"problem_id":problem,"contest_id":contest,
                  "submitted_at":data["submitted_at"],"expected_verdict":verdict,"expected_score":score,
                  "language":language,"accepted_at_monotonic":start,"user_token":user["token"]}
        self.records.append(record)
        return record

    def wait_results(self, records, timeout=300):
        deadline = time.monotonic() + timeout
        remaining = {r["id"]:r for r in records}
        while remaining and time.monotonic()<deadline:
            for ident, record in list(remaining.items()):
                result = self.call("/submissions/"+str(ident),token=self.admin["token"])
                if result["verdict"] in TERMINAL:
                    record["actual_verdict"] = result["verdict"]
                    record["actual_score"] = result["score"]
                    record["cases"] = [{k:v for k,v in c.items() if k in {"status","exit_code","time_used","memory_used","score","stderr"}} for c in result["case_results"]]
                    self.check(f"submission {ident}: {record['language']} {record['expected_verdict']} / {record['expected_score']}",
                        (result["verdict"],result["score"])==(record["expected_verdict"],record["expected_score"]))
                    self.check(f"submission {ident}: case results are unique", len({c["case_id"] for c in result["case_results"]})==len(result["case_results"]))
                    record["end_to_end_seconds"] = round(time.monotonic()-record["accepted_at_monotonic"],2)
                    remaining.pop(ident)
            if remaining:
                time.sleep(.5)
        self.check("all accepted submissions reached expected terminal results",not remaining)

    def expect_rank(self, contest, frozen=False, staff=False):
        records = [r for r in self.records if r["contest_id"]==contest["id"]]
        cutoff = (instant(contest["end_at"])-timedelta(minutes=1)).isoformat() if frozen else None
        weights = {p["problem"]:p["score"] for p in contest["contest_problems"]}
        expected = rank(contest["rule"],records,contest["start_at"],weights,cutoff)
        result = self.call(f"/contests/{contest['id']}/ranklist",token=(self.admin if staff else self.students[0])["token"])
        self.report.setdefault("rank_comparisons",[]).append({"rule":contest["rule"],"contest_id":contest["id"],"frozen":frozen,"staff":staff,"expected":expected,"actual":normalize(result["results"])})
        self.check(contest["rule"] + (" staff" if staff else " member") + (" frozen" if frozen else " final") + " ranking matches independent fixture oracle",
                   normalize(result["results"])==expected and result["frozen"]==frozen)

    def contests(self):
        now = datetime.now(timezone.utc)
        start = (now+timedelta(seconds=8)).isoformat()
        end = (now+timedelta(seconds=300)).isoformat()
        self.acm = self.create_contest("ACM",start,end)
        self.ioi = self.create_contest("IOI",start,end)
        self.private = self.create_contest("ACM",start,end,True)
        student = self.students[0]
        self.check("upcoming contest hides problems",not self.call(f"/contests/{self.acm['id']}",token=student["token"])["contest_problems"])
        self.call("/submissions","POST",{"problem":self.problems[0]["id"],"contest":self.acm["id"],"language":"PYTHON","code":GOOD["PYTHON"]},student["token"],expected=400)
        self.call(f"/contests/{self.private['id']}",token=self.students[-1]["token"],expected=404)
        self.call("/problems/"+str(self.hidden["id"]),token=student["token"],expected=404)
        self.call("/problems","POST",self.problem(7),student["token"],expected=403)
        self.call("/users/"+str(student["id"]),"PATCH",{"role":"ADMIN"},student["token"],expected=403)
        self.check("upcoming submission and member privilege escalation denied")
        while datetime.now(timezone.utc)<instant(start): time.sleep(.2)
        self.check("contest naturally transitions to running",len(self.call(f"/contests/{self.acm['id']}",token=student["token"])["contest_problems"])==6)
        def attempt(pair):
            index, user = pair
            bad = index % 5 == 0
            code = "print(0)" if bad else "a,b=map(int,input().split());print("+EXPRESSIONS[index%6]+")"
            return self.submit(user,self.problems[index%6]["id"],code,"WRONG_ANSWER" if bad else "ACCEPTED",0 if bad else 100,contest=self.acm["id"])
        with ThreadPoolExecutor(max_workers=20) as executor:
            first = list(executor.map(attempt,enumerate(self.students)))
        time.sleep(1.1)
        corrected = [self.submit(self.students[i],self.problems[i%6]["id"],"a,b=map(int,input().split());print("+EXPRESSIONS[i%6]+")",contest=self.acm["id"]) for i in range(0,20,5)]
        extras = []
        for index, language in enumerate(["C","CPP","JAVA"]):
            extras.append(self.submit(self.students[index+1],self.problems[0]["id"],GOOD[language],language=language))
        errors = [("CPP","invalid C++ source","COMPILE_ERROR"),("PYTHON","raise RuntimeError('fixture')","RUNTIME_ERROR"),("PYTHON","while True: pass","TIME_LIMIT_EXCEEDED"),("PYTHON","print('x'*600000)","OUTPUT_LIMIT_EXCEEDED"),("PYTHON","a=bytearray(1024**3)","MEMORY_LIMIT_EXCEEDED")]
        for index,(language,code,verdict) in enumerate(errors):
            target = self.memory_problem["id"] if verdict=="MEMORY_LIMIT_EXCEEDED" else self.problems[0]["id"]
            extras.append(self.submit(self.students[index+7],target,code,verdict,0,language))
        partial = "a,b=map(int,input().split());print(a+b if a>0 else 0)"
        for index,user in enumerate(self.students[12:15]):
            self.submit(user,self.problems[0]["id"],partial if index==0 else GOOD["PYTHON"],"WRONG_ANSWER" if index==0 else "ACCEPTED",50 if index==0 else 100,contest=self.ioi["id"])
        time.sleep(1.1)
        for index,user in enumerate(self.students[12:15]):
            self.submit(user,self.problems[1]["id"],"a,b=map(int,input().split());print(a-b)",contest=self.ioi["id"])
        self.wait_results(list(self.records))
        self.expect_rank(self.acm)
        self.expect_rank(self.ioi)
        own = self.records[0]
        self.call("/submissions/"+str(own["id"]),token=self.students[-1]["token"],expected=403)
        self.check("other members cannot read submission source")
        timing = [r["end_to_end_seconds"] for r in self.records]
        self.report["judge_load"]={"virtual_students":20,"submissions":len(timing),"end_to_end_p50_s":round(statistics.median(timing),2),"end_to_end_max_s":max(timing),"worker_count":1}

    def load(self):
        def read(index):
            begin = time.monotonic()
            try:
                self.call(["/problems?search=Acceptance","/contests","/users/leaderboard"][index%3])
                return (time.monotonic()-begin)*1000,True
            except Exception: return (time.monotonic()-begin)*1000,False
        with ThreadPoolExecutor(max_workers=20) as pool:
            results = list(pool.map(read,range(400)))
        times = sorted(r[0] for r in results)
        self.report["read_load"]={"requests":400,"clients":20,"errors":sum(not r[1] for r in results),"p95_ms":round(times[int(len(times)*.95)-1],2),"acceptance_p95_ms":2000}
        self.check("20-client read burst has no errors and P95 below 2000ms",all(r[1] for r in results) and times[379]<2000)

    def memory_probe(self):
        problem = self.call("/problems","POST",self.problem(0),self.admin["token"])
        record = self.submit(self.admin,problem["id"],"a=bytearray(1024**3)","MEMORY_LIMIT_EXCEEDED",0)
        self.wait_results([record],90)

    def faults(self):
        user = self.students[16]
        try:
            self.compose("stop","rabbit")
            record = self.submit(user,self.problems[0]["id"],GOOD["PYTHON"])
            time.sleep(3)
            self.check("broker outage preserves pending submission and outbox",self.call("/submissions/"+str(record["id"]),token=user["token"])["verdict"]=="PENDING" and int(self.sql(f"SELECT COUNT(*) FROM judge_outbox WHERE submission_id={record['id']} AND sent_at IS NULL;"))>0)
        finally: self.compose("start","rabbit")
        self.wait_results([record],150)
        self.rabbit = "http://" + self.compose("port","rabbit","15672")
        before = self.call("/submissions/"+str(record["id"]),token=user["token"])
        header = {"Content-Type":"application/json","Authorization":"Basic "+base64.b64encode(("oj:"+self.secret).encode()).decode()}
        for _ in range(2):
            body={"properties":{"delivery_mode":2},"routing_key":"oj.judge.v1","payload":str(record["id"]),"payload_encoding":"string"}
            request=urllib.request.Request(self.rabbit+"/api/exchanges/%2F/amq.default/publish",data=json.dumps(body).encode(),headers=header,method="POST")
            with HTTP.open(request,timeout=15) as response: assert json.load(response)["routed"]
        time.sleep(3)
        after = self.call("/submissions/"+str(record["id"]),token=user["token"])
        self.check("duplicate messages do not rejudge or duplicate case results",before["judged_at"]==after["judged_at"] and before["case_results"]==after["case_results"])
        time.sleep(1.1)
        interrupted = self.submit(self.students[17],self.problems[0]["id"],"import time;time.sleep(.8);"+GOOD["PYTHON"])
        for _ in range(100):
            if self.call("/submissions/"+str(interrupted["id"]),token=self.admin["token"])["verdict"]=="JUDGING": break
            time.sleep(.1)
        try:
            self.compose("kill","-s","SIGKILL","judge")
            self.sql(f"UPDATE submission SET lease_until=DATE_SUB(NOW(6),INTERVAL 1 SECOND) WHERE id={interrupted['id']} AND verdict='JUDGING';")
        finally: self.compose("start","judge")
        self.wait_results([interrupted],150)
        self.check("interrupted worker lease is retried after injected expiration",int(self.sql(f"SELECT judge_attempts FROM submission WHERE id={interrupted['id']};"))>=2)
        self.report["lease_fault"]="Actual worker SIGKILL; expiration injected only in disposable test DB; real recovery scheduler and queue used."
        self.compose("restart","api")
        self.base = "http://" + self.compose("port","api","8088") + "/api"
        for _ in range(90):
            try:
                if self.call("/auth/me",token=user["token"])["id"]==user["id"]: break
            except Exception: time.sleep(.5)
        self.check("sessions and submission results survive API restart",self.call("/submissions/"+str(record["id"]),token=user["token"])["verdict"]=="ACCEPTED")

    def phases(self):
        cutoff = instant(self.acm["end_at"])-timedelta(minutes=1)
        while datetime.now(timezone.utc)<=cutoff: time.sleep(.5)
        # If prior stages ran unusually slowly, fail instead of claiming to test a missed phase.
        self.check("freeze phase reached before contest ends",datetime.now(timezone.utc)<instant(self.acm["end_at"])-timedelta(seconds=8))
        late = self.submit(self.students[0],self.problems[5]["id"],"a,b=map(int,input().split());print(abs(a-b))",contest=self.acm["id"])
        self.wait_results([late],80)
        self.expect_rank(self.acm,True)
        self.expect_rank(self.acm,True,True)
        self.expect_rank(self.ioi,True)
        while datetime.now(timezone.utc)<instant(self.acm["end_at"]): time.sleep(.5)
        self.expect_rank(self.acm)
        self.expect_rank(self.ioi)
        self.call("/submissions","POST",{"problem":self.problems[0]["id"],"contest":self.acm["id"],"language":"PYTHON","code":GOOD["PYTHON"]},self.students[0]["token"],expected=400)
        self.check("contest naturally ends, unfreezes, and rejects late submissions")
        self.report["contest_phases"]="Natural wall-clock upcoming/running/frozen/ended; start and end were not changed after creation."

    def migration(self):
        # Run the existing real PostgreSQL -> MySQL suite in a private workspace.
        # Its ROOT/.env and Compose commands therefore point exclusively at this test project.
        self.compose("stop","judge")
        shutil.copytree(ROOT/"migration",self.work/"migration",ignore=shutil.ignore_patterns("__pycache__"))
        schema = self.work/"backend/src/main/resources/db/migration"
        schema.mkdir(parents=True)
        for source in (ROOT/"backend/src/main/resources/db/migration").glob("*.sql"):
            shutil.copy2(source,schema/source.name)
        output=command([sys.executable,"migration/tests/roundtrip.py"],cwd=self.work,timeout=240)
        self.check("12 real PostgreSQL to MySQL migration and rollback checks", "PASS: 12 migration checks" in output)
        self.report["migration"]={"suite":"migration/tests/roundtrip.py","checks":12,"source":"generated PostgreSQL fixture, never the user's old DB"}

    def differential(self):
        from differential import replay
        self.compose("stop","judge")
        replay(self,command,ROOT)

    def cleanup(self):
        # Docker sandbox resources have an exact, unique ownership label.
        self.compose("stop","judge")
        for resource in ("container","volume"):
            ids=command(["docker",resource,"ls","-aq" if resource=="container" else "-q","--filter","label=duilio.oj.namespace="+self.project]).splitlines()
            for ident in ids:
                data=json.loads(command(["docker",resource,"inspect",ident]))[0]
                labels=(data.get("Config",{}).get("Labels") or {}) if resource=="container" else data.get("Labels",{})
                assert labels.get("duilio.oj.namespace")==self.project
                command(["docker",resource,"rm",*( ["-f"] if resource=="container" else []),ident])
        self.compose("down","--volumes","--remove-orphans",timeout=120)
        for resource in ("container","volume"):
            remaining=command(["docker",resource,"ls","-aq" if resource=="container" else "-q","--filter","label=duilio.oj.namespace="+self.project])
            assert not remaining, "Owned test resources remain after cleanup"


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keep",action="store_true",help="Keep only this generated test environment for debugging")
    parser.add_argument("--probe-memory",action="store_true",help="Run only the isolated memory-limit regression")
    parser.add_argument("--probe-differential",action="store_true",help="Run only isolated legacy/Java contract replay")
    args=parser.parse_args()
    test=Acceptance()
    success=False
    try:
        stages = [("isolation",test.setup),("fixtures",test.fixtures),("browser",test.browser),
                            ("contest and judging",test.contests),("read workload",test.load),("fault recovery",test.faults),
                            ("freeze and finish",test.phases),("data migration",test.migration),("legacy/Java replay",test.differential)]
        if args.probe_memory: stages = [("isolation",test.setup),("memory regression",test.memory_probe)]
        if args.probe_differential: stages = [("isolation",test.setup),("legacy/Java replay",test.differential)]
        test.report["mode"] = "memory regression" if args.probe_memory else "legacy/Java replay" if args.probe_differential else "full"
        for name,action in stages:
            test.stage(name,action)
        success=True
    except Exception as error:
        test.report["failure"]={"type":type(error).__name__,"message":str(error)}
        (test.work/"failure.log").write_text(traceback.format_exc(),encoding="utf-8")
        try: (test.work/"services.log").write_text(test.compose("logs","--no-color"),encoding="utf-8")
        except Exception: pass
    finally:
        if not args.keep and test.compose_file.exists():
            try: test.cleanup(); test.report["cleanup"]="owned test resources removed"
            except Exception as error: test.report["cleanup"]="failed: "+str(error); success=False
        test.report["success"]=success
        test.report["finished_at"]=datetime.now(timezone.utc).isoformat()
        test.save()
    print("REPORT " + str(test.work/"report.json"),flush=True)
    print("PASS" if success else "FAILED",flush=True)
    return 0 if success else 1


if __name__=="__main__":
    sys.exit(main())
