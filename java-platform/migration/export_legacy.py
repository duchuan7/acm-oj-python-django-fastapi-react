"""Run inside the OLD Django backend: python - < export_legacy.py > legacy.json
Exports a consistent PostgreSQL snapshot and embeds testcase files. Does not modify the old database.
"""
import json, os, sys
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, str(Path.cwd()))
import django
django.setup()
from django.apps import apps
from django.core import serializers
from django.db import connection, transaction

LABELS = [
    "accounts.User", "problems.Problem", "problems.TestCase", "contests.Contest",
    "contests.ContestProblem", "submissions.Submission", "submissions.SubmissionCaseResult",
    "problems.ProblemProposal", "problems.ProblemSolution", "blogs.BlogPost", "contests.ContestRankSnapshot",
]
root = Path(os.environ.get("TESTCASE_ROOT", "/data/testcases")).resolve()
with transaction.atomic():
    if connection.vendor == "postgresql":
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
    objects, files = [], {}
    for label in LABELS:
        model = apps.get_model(label)
        objects.extend(json.loads(serializers.serialize("json", model.objects.all().order_by("pk"))))
    for case in apps.get_model("problems.TestCase").objects.all():
        embedded = {}
        for key, value in [("input", case.input_file), ("output", case.output_file)]:
            path = Path(value) if Path(value).is_absolute() else root / value
            path = path.resolve()
            if not path.is_relative_to(root):
                raise RuntimeError("Testcase path is outside TESTCASE_ROOT: " + str(case.pk))
            if path.stat().st_size > 1048576:
                raise RuntimeError("Testcase is larger than 1 MiB: " + str(case.pk))
            embedded[key] = path.read_text(encoding="utf-8")
        files[str(case.pk)] = embedded
    payload = {"format": "duilio-oj-legacy-v1", "objects": objects, "testcase_files": files}
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)

