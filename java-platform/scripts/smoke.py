"""End-to-end checks against a running development stack. Uses only Python's standard library."""
import json, re, secrets, time, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8088/api"
MAIL = "http://127.0.0.1:8026"
HTTP = urllib.request.build_opener(urllib.request.ProxyHandler({}))
CHECKS = []

def call(path, method="GET", body=None, token=None, expected=200, base=BASE):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request(base + path, data=None if body is None else json.dumps(body).encode(), headers=headers, method=method)
    try:
        with HTTP.open(request, timeout=30) as response:
            status, data = response.status, json.load(response)
    except urllib.error.HTTPError as error:
        status = error.code
        raw = error.read()
        data = json.loads(raw) if raw else {}
    assert status == expected, f"{method} {path}: expected {expected}, got {status}: {data}"
    return data

def check(name, condition=True):
    assert condition, name
    CHECKS.append(name)
    print("PASS " + name, flush=True)

def mailbox_code(address):
    for _ in range(30):
        messages = call("/api/v1/messages", base=MAIL).get("messages", [])
        for message in messages:
            if any(person["Address"].lower() == address for person in message.get("To", [])):
                detail = call("/api/v1/message/" + message["ID"], base=MAIL)
                match = re.search(r"code is ([0-9]{6})", detail["Text"])
                if match:
                    return match.group(1)
        time.sleep(0.3)
    raise AssertionError("Verification email not received")

def login(username, password):
    return call("/auth/login", "POST", {"username": username, "password": password})

def problem(slug, public=True):
    return dict(title=slug, slug=slug, description="Sum two integers", input_description="a b",
                output_description="a+b", samples=[{"input": "1 2\n", "output": "3\n"}],
                time_limit_ms=1000, memory_limit_mb=256, difficulty=800, tags=["smoke"],
                source="Automated verification", is_public=public,
                test_cases=[dict(order=1, input="1 2\n", output="3\n", score=50, is_sample=True),
                            dict(order=2, input="-100 42\n", output="-58\n", score=50, is_sample=False)])

def run():
    env = dict(line.split("=", 1) for line in (ROOT / ".env").read_text().splitlines() if "=" in line and not line.startswith("#"))
    administrator = login(env["ADMIN_USERNAME"], env["ADMIN_PASSWORD"])
    at = administrator["token"]
    check("administrator JWT login", call("/auth/me", token=at)["role"] == "ADMIN")
    cache = ROOT / ".runtime" / "smoke-users.json"
    if cache.exists():
        accounts = json.loads(cache.read_text())
    else:
        accounts = []
        suffix = secrets.token_hex(4)
        for label in ["alice", "bob", "coach"]:
            name = "smoke_" + label + "_" + suffix
            address = name + "@example.test"
            password = secrets.token_hex(12)
            call("/auth/registration-code", "POST", {"email": address})
            code = mailbox_code(address)
            account = call("/auth/register", "POST", {"username": name, "email": address, "password": password, "code": code, "school": "smoke"})
            accounts.append({"username": name, "password": password, "id": account["user"]["id"], "email": address})
        call("/users/" + str(accounts[2]["id"]), "PATCH", {"role": "COACH"}, at)
        cache.parent.mkdir(exist_ok=True)
        cache.write_text(json.dumps(accounts))
    sessions = [login(a["username"], a["password"]) for a in accounts]
    alice, bob, coach = [s["token"] for s in sessions]
    check("email-verified registration and role separation", sessions[0]["user"]["role"] == "MEMBER" and sessions[2]["user"]["role"] == "COACH")
    suffix = secrets.token_hex(5)
    draft = problem("smoke-public-" + suffix)
    public = call("/problems", "POST", draft, at)
    pid = public["id"]
    hidden = call("/problems", "POST", problem("smoke-private-" + suffix, False), at)
    call("/problems/" + str(hidden["id"]), expected=404)
    call("/problems/" + str(hidden["id"]), token=alice, expected=404)
    check("private problems resist anonymous and member enumeration")
    call("/problems", "POST", problem("smoke-denied-" + suffix), alice, expected=403)
    call("/users/" + str(accounts[0]["id"]), "PATCH", {"role": "ADMIN"}, alice, expected=403)
    check("members cannot manage problems or escalate roles")
    detail = call("/problems/" + str(pid))
    check("public problem responses do not expose hidden testcases", "test_cases" not in detail)
    check("exact tag filter works on MySQL 8.4", any(p["id"] == pid for p in call("/problems?tag=smoke")["results"]))
    call("/submissions", "POST", {"problem": pid, "language": "CPP", "code": "x"}, expected=401)
    call("/submissions", "POST", {"problem": hidden["id"], "language": "CPP", "code": "x"}, alice, expected=403)
    check("submission authentication and private problem checks")
    reset_email = accounts[0]["email"]
    call("/auth/password-reset-code", "POST", {"email": reset_email})
    reset_code = mailbox_code(reset_email)
    new_password = secrets.token_hex(12)
    call("/auth/password-reset", "POST", {"email": reset_email, "code": "invalid", "password": new_password}, expected=400)
    old_password = accounts[0]["password"]
    call("/auth/password-reset", "POST", {"email": reset_email, "code": reset_code, "password": new_password})
    accounts[0]["password"] = new_password
    cache.write_text(json.dumps(accounts))
    call("/auth/me", token=alice, expected=401)
    call("/auth/login", "POST", {"username": accounts[0]["username"], "password": old_password}, expected=401)
    alice = login(accounts[0]["username"], new_password)["token"]
    call("/auth/password-reset", "POST", {"email": reset_email, "code": reset_code, "password": new_password}, expected=400)
    check("password reset verifies email, rejects reused codes, and invalidates prior sessions")
    blog = call("/blogs", "POST", {"title": "smoke draft", "content": "private draft", "status": "DRAFT"}, alice)
    call("/blogs/" + str(blog["id"]), expected=404)
    call("/blogs/" + str(blog["id"]), "PUT", {"title": "stolen", "content": "x", "status": "PUBLISHED"}, bob, expected=404)
    call("/blogs/" + str(blog["id"]), "PUT", {"title": "smoke published", "content": "published content", "status": "PUBLISHED"}, alice)
    check("blog drafts stay private and authors can publish", call("/blogs/" + str(blog["id"]))["status"] == "PUBLISHED")
    editorial = call("/problem-solutions", "POST", {"problem": pid, "title": "smoke editorial", "content": "Use addition."}, alice)
    eid = editorial["id"]
    call("/problem-solutions/" + str(eid), expected=404)
    call("/problem-solutions/" + str(eid) + "/approve", "POST", {}, alice, expected=403)
    call("/problem-solutions/" + str(eid) + "/approve", "POST", {"review_message": "OK"}, at)
    check("editorial approval controls public visibility", call("/problem-solutions/" + str(eid))["status"] == "APPROVED")
    call("/problem-solutions/" + str(eid), "PUT", {"problem": pid, "title": "edited", "content": "New explanation"}, alice)
    call("/problem-solutions/" + str(eid), expected=404)
    check("editing an approved editorial returns it to review")
    proposal = call("/problem-proposals", "POST", {"problem": problem("smoke-proposal-" + suffix), "standard_language": "PYTHON", "standard_code": "a,b=map(int,input().split());print(a+b)"}, alice)
    approved = call("/problem-proposals/" + str(proposal["id"]) + "/approve", "POST", {"review_message": "Approved"}, at)
    call("/problem-proposals/" + str(proposal["id"]) + "/approve", "POST", {}, at, expected=409)
    check("proposal approval creates one public problem atomically", call("/problems/" + str(approved["approved_problem"]))["is_public"])
    start = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - 120))
    end = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + 1800))
    contest_data = dict(title="smoke private " + suffix, description="private training", rule="ACM", start_at=start,
                        end_at=end, is_public=False, freeze_rank_minutes=0, participants=[],
                        contest_problems=[dict(problem=None, new_problem=problem("smoke-contest-" + suffix), alias="A", score=100, order=1),
                                          dict(problem=pid, new_problem=None, alias="B", score=100, order=2)])
    contest = call("/contests", "POST", contest_data, alice)
    cid, cpid = contest["id"], contest["contest_problems"][0]["problem"]
    call("/contests/" + str(cid), token=bob, expected=404)
    call("/problems/" + str(cpid), token=alice, expected=404)
    call("/problems/" + str(cpid) + "?contest=" + str(cid), token=alice)
    check("contest-only problems require contest visibility")
    private_submission = call("/submissions", "POST", {
        "problem": pid, "contest": cid, "language": "PYTHON",
        "code": "a,b=map(int,input().split());print(a+b)"}, alice)
    check("private contest submission metadata stays hidden from non-participants",
          call("/submissions?problem=" + str(pid), token=bob)["count"] == 0
          and call("/submissions?problem=" + str(pid), token=alice)["count"] == 1)
    time.sleep(1.05)
    denied = dict(contest_data, is_public=True, contest_problems=[])
    call("/contests", "POST", denied, alice, expected=403)
    check("only admins can create public contests")
    frozen = call("/contests", "POST", dict(contest_data, title="smoke frozen " + suffix,
                  end_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time()+30)),
                  freeze_rank_minutes=1, contest_problems=[dict(problem=pid, new_problem=None, alias="A", score=100, order=1)]), at)
    check("rank freeze is reported", call("/contests/" + str(frozen["id"]) + "/ranklist", token=at)["frozen"])
    jobs = [
        ("CPP", '#include <iostream>\nint main(){long long a,b;std::cin>>a>>b;std::cout<<a+b<<"\\n";}', "ACCEPTED"),
        ("C", '#include <stdio.h>\nint main(){long long a,b;scanf("%lld%lld",&a,&b);printf("%lld\\n",a+b);}', "ACCEPTED"),
        ("JAVA", 'import java.util.*; public class Main{public static void main(String[] args){Scanner s=new Scanner(System.in);System.out.println(s.nextLong()+s.nextLong());}}', "ACCEPTED"),
        ("PYTHON", "a,b=map(int,input().split());print(a+b)", "ACCEPTED"),
        ("PYTHON", "print(0)", "WRONG_ANSWER"),
        ("CPP", "this is invalid c++", "COMPILE_ERROR"),
        ("CPP", "int main(){return 1;}", "RUNTIME_ERROR"),
        ("CPP", "int main(){for(;;){}}", "TIME_LIMIT_EXCEEDED"),
        ("CPP", '#include <cstdio>\nint main(){while(true)puts("0123456789012345678901234567890123456789");}', "OUTPUT_LIMIT_EXCEEDED"),
        ("CPP", '#include <vector>\nint main(){std::vector<std::vector<char>> a;while(true)a.emplace_back(8*1024*1024,1);}', "MEMORY_LIMIT_EXCEEDED"),
        ("PYTHON", "import socket\ns=socket.socket();s.settimeout(0.2);s.connect(('1.1.1.1',80))", "RUNTIME_ERROR"),
        ("PYTHON", "open('/etc/oj-forbidden','w').write('x')", "RUNTIME_ERROR"),
    ]
    tokens = [at, alice, bob, coach]
    submitted = [(private_submission["id"], "ACCEPTED", alice)]
    for index, (lang, code, verdict) in enumerate(jobs):
        token = tokens[index % len(tokens)]
        row = call("/submissions", "POST", {"problem": pid, "language": lang, "code": code}, token)
        submitted.append((row["id"], verdict, token))
        time.sleep(0.35)
    first = submitted[1]
    call("/submissions/" + str(first[0]), token=bob, expected=403)
    check("another user cannot read submission source")
    pending = list(submitted)
    deadline = time.time() + 240
    while pending and time.time() < deadline:
        for job in list(pending):
            row = call("/submissions/" + str(job[0]), token=job[2])
            if row["verdict"] not in ["PENDING", "JUDGING"]:
                assert row["verdict"] == job[1], f"Submission {job[0]} expected {job[1]}, got {row['verdict']}: {row.get('compile_message')}"
                if row["verdict"] == "ACCEPTED":
                    assert row["score"] == 100 and len(row["case_results"]) == 2
                if job[2] != at and job[2] != coach:
                    assert all("stdout" not in r and "stderr" not in r for r in row["case_results"])
                check("Docker judge " + str(job[0]) + " => " + job[1])
                pending.remove(job)
        time.sleep(0.5)
    assert not pending, f"Judge jobs did not finish: {pending}"
    check("all four languages and all verdict branches passed")
    test_code = "print('x'*65537)"
    call("/submissions", "POST", {"problem": pid, "language": "PYTHON", "code": "中"*22000}, alice, expected=400)
    check("64 KiB limit counts UTF-8 bytes")
    profile = call("/users/" + str(accounts[0]["id"]) + "/profile")
    check("public profile includes public submission metadata without source", "submissions" in profile and all("code" not in s for s in profile["submissions"]))
    call("/auth/logout", "POST", {}, bob)
    call("/auth/me", token=bob, expected=401)
    check("logout invalidates existing JWTs")
    summary = {"checks": CHECKS, "submission_ids": [j[0] for j in submitted], "problem_ids": [pid, hidden["id"], approved["approved_problem"], cpid],
               "contest_ids": [cid, frozen["id"]], "blog_id": blog["id"], "editorial_id": eid, "proposal_id": proposal["id"]}
    (ROOT / ".runtime" / "smoke-result.json").write_text(json.dumps(summary, indent=2))
    print(f"PASS: {len(CHECKS)} checks", flush=True)

if __name__ == "__main__":
    run()
