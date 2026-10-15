"""Verify broker outage recovery and duplicate delivery against the local Compose stack."""
import base64, json, subprocess, sys, time, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from smoke import ROOT, call, login, HTTP

def compose(*args):
    subprocess.run(["docker", "compose", *args], cwd=ROOT, check=True, capture_output=True)

def main():
    env = dict(line.split("=",1) for line in (ROOT/".env").read_text().splitlines() if "=" in line and not line.startswith("#"))
    token = login(env["ADMIN_USERNAME"], env["ADMIN_PASSWORD"])["token"]
    try:
        compose("stop", "rabbit")
        submission = call("/submissions","POST",{"problem":1,"language":"PYTHON","code":"a,b=map(int,input().split());print(a+b)"},token)
        ident = submission["id"]
        time.sleep(3)
        assert call("/submissions/"+str(ident),token=token)["verdict"]=="PENDING"
        print("PASS submission persisted while RabbitMQ was offline",flush=True)
    finally:
        compose("start","rabbit")
    deadline=time.time()+120
    while time.time()<deadline:
        result=call("/submissions/"+str(ident),token=token)
        if result["verdict"] not in ["PENDING","JUDGING"]:
            break
        time.sleep(1)
    assert result["verdict"]=="ACCEPTED",result["verdict"]
    print("PASS outbox delivered the task after broker recovery",flush=True)
    message={"properties":{"delivery_mode":2},"routing_key":"oj.judge.v1","payload":str(ident),"payload_encoding":"string"}
    headers={"Content-Type":"application/json","Authorization":"Basic "+base64.b64encode(("oj:"+env["RABBIT_PASSWORD"]).encode()).decode()}
    for _ in range(2):
        request=urllib.request.Request("http://127.0.0.1:15673/api/exchanges/%2F/amq.default/publish",
            data=json.dumps(message).encode(),headers=headers,method="POST")
        with HTTP.open(request,timeout=15) as response:
            assert json.load(response)["routed"]
    time.sleep(3)
    after=call("/submissions/"+str(ident),token=token)
    assert after["verdict"]=="ACCEPTED" and after["judged_at"]==result["judged_at"]
    assert len(after["case_results"])==len(result["case_results"])
    print("PASS duplicate deliveries did not rejudge or duplicate results",flush=True)
    print("PASS: 3 reliability checks",flush=True)

if __name__=="__main__":
    main()
