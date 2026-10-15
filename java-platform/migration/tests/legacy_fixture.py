"""Generate an isolated Django fixture and export it. Run in the legacy backend image."""
import datetime, os, runpy, sys
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, "/app")
from django.conf import settings
if os.environ.get("MIGRATION_TEST_POSTGRES") == "true":
    settings.DATABASES = {"default": {
        "ENGINE": "django.db.backends.postgresql", "NAME": "source", "USER": "legacy",
        "PASSWORD": "", "HOST": "127.0.0.1", "PORT": 5432
    }}
else:
    settings.DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
import django
django.setup()
from django.core.management import call_command
from django.utils import timezone
from apps.accounts.models import User
from apps.problems.models import Problem, TestCase, ProblemProposal, ProblemSolution
from apps.contests.models import Contest, ContestProblem, ContestRankSnapshot
from apps.submissions.models import Submission, SubmissionCaseResult
from apps.blogs.models import BlogPost

call_command("migrate", verbosity=0)
admin = User.objects.create_user(id=101, username="legacy_admin", email="admin@example.test", password="legacy-password", role="ADMIN")
member = User.objects.create_user(id=102, username="legacy_member", email="member@example.test", password="legacy-member-password")
problem = Problem.objects.create(id=201, title="迁移测试 ' quotes \\ path", slug="legacy-sum", description="你好，世界。",
    input_description="a b", output_description="a+b", samples=[{"input": "1 2\n", "output": "3\n"}],
    time_limit_ms=1000, memory_limit_mb=256, difficulty=800, tags=["math", "入门"], source="fixture", is_public=True, created_by=admin)
root = Path("/data/testcases")
root.mkdir(parents=True, exist_ok=True)
(root / "1.in").write_text("1 2\n", encoding="utf-8")
(root / "1.out").write_text("3\n", encoding="utf-8")
case = TestCase.objects.create(id=301, problem=problem, order=1, input_file="1.in", output_file="1.out", score=100, is_sample=True)
contest = Contest.objects.create(id=401, title="旧比赛", rule="ACM", start_at=timezone.now()-datetime.timedelta(hours=2),
    end_at=timezone.now()-datetime.timedelta(hours=1), is_public=False, created_by=admin)
contest.participants.add(member)
ContestProblem.objects.create(id=402, contest=contest, problem=problem, alias="A", score=100, order=1)
accepted = Submission.objects.create(id=501, user=member, problem=problem, contest=contest, language="PYTHON",
    code="print(sum(map(int,input().split())))", code_size=34, verdict="ACCEPTED", score=100, judged_at=timezone.now())
SubmissionCaseResult.objects.create(id=601, submission=accepted, case=case, status="ACCEPTED", time_used=12,
    memory_used=5000, exit_code=0, stdout="3\n", stderr="", score=100)
for ident, verdict in [(502, "PENDING"), (503, "JUDGING")]:
    Submission.objects.create(id=ident, user=member, problem=problem, language="CPP", code="int main(){}", code_size=12, verdict=verdict)
ProblemProposal.objects.create(id=701, author=member, title=problem.title, slug="legacy-approved", description="statement",
    input_description="input", output_description="output", samples=[], standard_language="CPP", standard_code="int main(){}",
    status="APPROVED", approved_problem=problem, reviewed_by=admin, reviewed_at=timezone.now())
ProblemProposal.objects.create(id=702, author=member, title="pending", slug="legacy-pending", description="statement",
    input_description="input", output_description="output", samples=[], standard_language="CPP", standard_code="int main(){}")
ProblemSolution.objects.create(id=801, problem=problem, author=member, title="旧题解", content="解释", status="APPROVED", reviewed_by=admin)
BlogPost.objects.create(id=901, author=member, title="旧博客", content="<script>plain text</script>", status="PUBLISHED")
ContestRankSnapshot.objects.create(id=1001, contest=contest, frozen=True, payload={"rows": [{"username": "legacy_member", "solved": 1}]})
runpy.run_path("/migration/export_legacy.py", run_name="__main__")
