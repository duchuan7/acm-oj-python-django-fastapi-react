"""Remove only this checkout's recorded smoke-test fixtures. Dry-run by default."""
import argparse, importlib.util, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("importer",ROOT/"migration"/"import_legacy.py")
db=importlib.util.module_from_spec(spec)
spec.loader.exec_module(db)

def ids(sql):
    return [int(row) for row in db.mysql(sql).strip().splitlines() if row.strip()]

def sql_ids(values):
    return ",".join(str(int(value)) for value in values) or "NULL"

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply",action="store_true")
    parser.add_argument("--remove-test-users",action="store_true")
    args=parser.parse_args()
    cache=ROOT/".runtime"/"smoke-users.json"
    if not cache.exists():
        print("No recorded smoke users; nothing to clean.")
        return
    accounts=json.loads(cache.read_text())
    for account in accounts:
        assert account["username"].startswith("smoke_")
        actual=db.mysql("SELECT username FROM oj_user WHERE id="+str(int(account["id"]))+";").strip()
        if actual != account["username"]:
            raise RuntimeError("Test account identity does not match; no records were changed.")
    env=dict(line.split("=",1) for line in (ROOT/".env").read_text().splitlines() if "=" in line and not line.startswith("#"))
    test_users=[int(a["id"]) for a in accounts]
    allowed=test_users+ids("SELECT id FROM oj_user WHERE username="+db.value(env["ADMIN_USERNAME"])+";")
    owner_ids=sql_ids(allowed)
    problems=ids("SELECT id FROM problem WHERE source='Automated verification' AND slug LIKE 'smoke-%' AND created_by IN ("+owner_ids+");")
    contests=ids("SELECT id FROM contest WHERE title LIKE 'smoke %' AND created_by IN ("+owner_ids+");")
    pid,cid=sql_ids(problems),sql_ids(contests)
    submissions=ids("SELECT id FROM submission WHERE problem_id IN ("+pid+");")
    if db.mysql("SELECT COUNT(*) FROM submission WHERE problem_id IN ("+pid+") AND user_id NOT IN ("+owner_ids+");").strip() != "0":
        raise RuntimeError("A non-test user submitted to a fixture problem; refusing cleanup.")
    if db.mysql("SELECT COUNT(*) FROM submission WHERE contest_id IN ("+cid+") AND problem_id NOT IN ("+pid+");").strip() != "0":
        raise RuntimeError("A fixture contest has other submissions; refusing cleanup.")
    if db.mysql("SELECT COUNT(*) FROM submission WHERE id IN ("+sql_ids(submissions)+") AND verdict IN ('PENDING','JUDGING');").strip() != "0":
        raise RuntimeError("Fixture submissions are still being judged.")
    proposals=ids("SELECT id FROM problem_proposal WHERE author_id IN ("+owner_ids+") AND JSON_UNQUOTE(JSON_EXTRACT(problem_data,'$.source'))='Automated verification' AND JSON_UNQUOTE(JSON_EXTRACT(problem_data,'$.slug')) LIKE 'smoke-%';")
    blogs=ids("SELECT id FROM blog_post WHERE author_id IN ("+sql_ids(test_users)+") AND title IN ('smoke draft','smoke published');")
    print("Fixture candidates:",json.dumps({"problems":len(problems),"contests":len(contests),"submissions":len(submissions),"proposals":len(proposals),"blogs":len(blogs)}))
    if not args.apply:
        print("Dry-run only. No database changes.")
        return
    sid=sql_ids(submissions)
    statements=[
        "DELETE FROM case_result WHERE submission_id IN ("+sid+");",
        "DELETE FROM judge_outbox WHERE submission_id IN ("+sid+");",
        "DELETE FROM submission WHERE id IN ("+sid+");",
        "DELETE FROM problem_solution WHERE problem_id IN ("+pid+") AND author_id IN ("+owner_ids+");",
        "DELETE FROM problem_proposal WHERE id IN ("+sql_ids(proposals)+");",
        "DELETE FROM blog_post WHERE id IN ("+sql_ids(blogs)+");",
        "DELETE FROM contest_rank_snapshot WHERE contest_id IN ("+cid+");",
        "DELETE FROM contest_problem WHERE contest_id IN ("+cid+");",
        "DELETE FROM contest_participant WHERE contest_id IN ("+cid+");",
        "DELETE FROM contest WHERE id IN ("+cid+");",
        "DELETE FROM test_case WHERE problem_id IN ("+pid+");",
        "DELETE FROM problem WHERE id IN ("+pid+");",
    ]
    if args.remove_test_users:
        statements.append("DELETE FROM oj_user WHERE id IN ("+sql_ids(test_users)+");")
    db.mysql("START TRANSACTION;\n"+"\n".join(statements)+"\nCOMMIT;")
    if args.remove_test_users:
        cache.unlink()
    print("Committed cleanup of identified test fixtures. Other records and volumes were kept.")

if __name__=="__main__":
    main()
