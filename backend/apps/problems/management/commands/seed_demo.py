import os
from datetime import timedelta
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.contests.models import Contest, ContestProblem
from apps.problems.models import Problem, TestCase


class Command(BaseCommand):
    help = "Create demo admin, A+B problem, sample test cases, and a practice contest."

    def add_arguments(self, parser):
        parser.add_argument("--noinput", action="store_true", help="Run without prompts.")

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.getenv("DEMO_ADMIN_USERNAME", "admin")
        password = os.getenv("DEMO_ADMIN_PASSWORD", "change-me-local-admin-password")
        email = os.getenv("DEMO_ADMIN_EMAIL", "admin@example.com")

        admin, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "role": "ADMIN",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            admin.set_password(password)
            admin.save()
            self.stdout.write(self.style.SUCCESS(f"Created demo admin: {username}/{password}"))

        testcase_root = Path("/data/testcases/demo/a-plus-b")
        testcase_root.mkdir(parents=True, exist_ok=True)
        (testcase_root / "1.in").write_text("1 2\n", encoding="utf-8")
        (testcase_root / "1.out").write_text("3\n", encoding="utf-8")
        (testcase_root / "2.in").write_text("100 250\n", encoding="utf-8")
        (testcase_root / "2.out").write_text("350\n", encoding="utf-8")

        problem, _ = Problem.objects.update_or_create(
            slug="a-plus-b",
            defaults={
                "title": "A + B Problem",
                "description": "Read two integers a and b, then output their sum.",
                "input_description": "Two integers a and b.",
                "output_description": "One integer: a + b.",
                "samples": [{"input": "1 2\\n", "output": "3\\n"}],
                "time_limit_ms": 1000,
                "memory_limit_mb": 128,
                "is_public": True,
                "created_by": admin,
            },
        )
        TestCase.objects.update_or_create(
            problem=problem,
            order=1,
            defaults={
                "input_file": "demo/a-plus-b/1.in",
                "output_file": "demo/a-plus-b/1.out",
                "score": 50,
                "is_sample": True,
            },
        )
        TestCase.objects.update_or_create(
            problem=problem,
            order=2,
            defaults={
                "input_file": "demo/a-plus-b/2.in",
                "output_file": "demo/a-plus-b/2.out",
                "score": 50,
                "is_sample": False,
            },
        )

        now = timezone.now()
        contest, _ = Contest.objects.update_or_create(
            title="Demo Practice Contest",
            defaults={
                "description": "A small contest for smoke testing the OJ.",
                "rule": "ACM",
                "start_at": now,
                "end_at": now + timedelta(days=30),
                "is_public": True,
                "created_by": admin,
            },
        )
        ContestProblem.objects.update_or_create(
            contest=contest,
            problem=problem,
            defaults={"alias": "A", "score": 100, "order": 1},
        )
        self.stdout.write(self.style.SUCCESS("Demo data is ready."))
