import django.db.models.deletion
from django.db import migrations, models


VERDICT_CHOICES = [
    ("PENDING", "Pending"),
    ("JUDGING", "Judging"),
    ("ACCEPTED", "Accepted"),
    ("WRONG_ANSWER", "Wrong Answer"),
    ("TIME_LIMIT_EXCEEDED", "Time Limit Exceeded"),
    ("MEMORY_LIMIT_EXCEEDED", "Memory Limit Exceeded"),
    ("RUNTIME_ERROR", "Runtime Error"),
    ("COMPILE_ERROR", "Compile Error"),
    ("OUTPUT_LIMIT_EXCEEDED", "Output Limit Exceeded"),
    ("SYSTEM_ERROR", "System Error"),
]


def migrate_old_case_results(apps, schema_editor):
    Submission = apps.get_model("submissions", "Submission")
    OldCaseResult = apps.get_model("submissions", "JudgeCaseResult")
    NewCaseResult = apps.get_model("submissions", "SubmissionCaseResult")

    Submission.objects.filter(verdict="AC").update(verdict="ACCEPTED")
    for item in OldCaseResult.objects.all().iterator():
        status = "ACCEPTED" if item.verdict == "AC" else item.verdict
        NewCaseResult.objects.create(
            submission_id=item.submission_id,
            case_id=item.test_case_id,
            status=status,
            time_used=item.time_ms,
            memory_used=item.memory_kb,
            exit_code=None,
            stdout="",
            stderr="",
            score=item.score,
            message=item.message,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("problems", "0001_initial"),
        ("submissions", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="submission",
            name="verdict",
            field=models.CharField(choices=VERDICT_CHOICES, default="PENDING", max_length=32),
        ),
        migrations.CreateModel(
            name="SubmissionCaseResult",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=VERDICT_CHOICES, max_length=32)),
                ("time_used", models.PositiveIntegerField(default=0)),
                ("memory_used", models.PositiveIntegerField(default=0)),
                ("exit_code", models.IntegerField(blank=True, null=True)),
                ("stdout", models.TextField(blank=True)),
                ("stderr", models.TextField(blank=True)),
                ("score", models.PositiveIntegerField(default=0)),
                ("message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("case", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="problems.testcase")),
                (
                    "submission",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to="submissions.submission",
                    ),
                ),
            ],
            options={
                "db_table": "submission_case_result",
                "ordering": ["submission_id", "case_id"],
                "unique_together": {("submission", "case")},
            },
        ),
        migrations.RunPython(migrate_old_case_results, migrations.RunPython.noop),
        migrations.DeleteModel(name="JudgeCaseResult"),
        migrations.AlterField(
            model_name="submissioncaseresult",
            name="submission",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="case_results",
                to="submissions.submission",
            ),
        ),
    ]
