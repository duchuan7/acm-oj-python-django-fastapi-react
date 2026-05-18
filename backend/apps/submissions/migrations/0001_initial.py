# Generated for ACM Training OJ MVP.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("contests", "0001_initial"),
        ("problems", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Submission",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("language", models.CharField(choices=[("C", "C"), ("CPP", "C++"), ("JAVA", "Java"), ("PYTHON", "Python")], max_length=16)),
                ("code", models.TextField()),
                ("code_size", models.PositiveIntegerField()),
                ("verdict", models.CharField(choices=[("PENDING", "Pending"), ("JUDGING", "Judging"), ("AC", "Accepted"), ("WRONG_ANSWER", "Wrong Answer"), ("TIME_LIMIT_EXCEEDED", "Time Limit Exceeded"), ("MEMORY_LIMIT_EXCEEDED", "Memory Limit Exceeded"), ("COMPILE_ERROR", "Compile Error"), ("RUNTIME_ERROR", "Runtime Error"), ("SYSTEM_ERROR", "System Error")], default="PENDING", max_length=32)),
                ("score", models.PositiveIntegerField(default=0)),
                ("max_time_ms", models.PositiveIntegerField(default=0)),
                ("max_memory_kb", models.PositiveIntegerField(default=0)),
                ("compile_message", models.TextField(blank=True)),
                ("submitted_at", models.DateTimeField(auto_now_add=True)),
                ("judged_at", models.DateTimeField(blank=True, null=True)),
                ("contest", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="contests.contest")),
                ("problem", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="problems.problem")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-submitted_at"],
            },
        ),
        migrations.CreateModel(
            name="JudgeCaseResult",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("verdict", models.CharField(choices=[("PENDING", "Pending"), ("JUDGING", "Judging"), ("AC", "Accepted"), ("WRONG_ANSWER", "Wrong Answer"), ("TIME_LIMIT_EXCEEDED", "Time Limit Exceeded"), ("MEMORY_LIMIT_EXCEEDED", "Memory Limit Exceeded"), ("COMPILE_ERROR", "Compile Error"), ("RUNTIME_ERROR", "Runtime Error"), ("SYSTEM_ERROR", "System Error")], max_length=32)),
                ("time_ms", models.PositiveIntegerField(default=0)),
                ("memory_kb", models.PositiveIntegerField(default=0)),
                ("score", models.PositiveIntegerField(default=0)),
                ("message", models.TextField(blank=True)),
                ("submission", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="case_results", to="submissions.submission")),
                ("test_case", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="problems.testcase")),
            ],
            options={
                "ordering": ["submission_id", "test_case_id"],
                "unique_together": {("submission", "test_case")},
            },
        ),
        migrations.AddIndex(
            model_name="submission",
            index=models.Index(fields=["user", "-submitted_at"], name="submission_user_submit_idx"),
        ),
        migrations.AddIndex(
            model_name="submission",
            index=models.Index(fields=["problem", "verdict"], name="submission_problem_verdict_idx"),
        ),
        migrations.AddIndex(
            model_name="submission",
            index=models.Index(fields=["contest", "user"], name="submission_contest_user_idx"),
        ),
    ]
