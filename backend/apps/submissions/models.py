from django.conf import settings
from django.db import models


class Submission(models.Model):
    class Language(models.TextChoices):
        C = "C", "C"
        CPP = "CPP", "C++"
        JAVA = "JAVA", "Java"
        PYTHON = "PYTHON", "Python"

    class Verdict(models.TextChoices):
        PENDING = "PENDING", "Pending"
        JUDGING = "JUDGING", "Judging"
        AC = "AC", "Accepted"
        WRONG_ANSWER = "WRONG_ANSWER", "Wrong Answer"
        TIME_LIMIT_EXCEEDED = "TIME_LIMIT_EXCEEDED", "Time Limit Exceeded"
        MEMORY_LIMIT_EXCEEDED = "MEMORY_LIMIT_EXCEEDED", "Memory Limit Exceeded"
        COMPILE_ERROR = "COMPILE_ERROR", "Compile Error"
        RUNTIME_ERROR = "RUNTIME_ERROR", "Runtime Error"
        SYSTEM_ERROR = "SYSTEM_ERROR", "System Error"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    problem = models.ForeignKey("problems.Problem", on_delete=models.PROTECT)
    contest = models.ForeignKey("contests.Contest", null=True, blank=True, on_delete=models.PROTECT)
    language = models.CharField(max_length=16, choices=Language.choices)
    code = models.TextField()
    code_size = models.PositiveIntegerField()
    verdict = models.CharField(max_length=32, choices=Verdict.choices, default=Verdict.PENDING)
    score = models.PositiveIntegerField(default=0)
    max_time_ms = models.PositiveIntegerField(default=0)
    max_memory_kb = models.PositiveIntegerField(default=0)
    compile_message = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    judged_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-submitted_at"]
        indexes = [
            models.Index(fields=["user", "-submitted_at"]),
            models.Index(fields=["problem", "verdict"]),
            models.Index(fields=["contest", "user"]),
        ]


class JudgeCaseResult(models.Model):
    submission = models.ForeignKey(Submission, related_name="case_results", on_delete=models.CASCADE)
    test_case = models.ForeignKey("problems.TestCase", on_delete=models.PROTECT)
    verdict = models.CharField(max_length=32, choices=Submission.Verdict.choices)
    time_ms = models.PositiveIntegerField(default=0)
    memory_kb = models.PositiveIntegerField(default=0)
    score = models.PositiveIntegerField(default=0)
    message = models.TextField(blank=True)

    class Meta:
        unique_together = [("submission", "test_case")]
        ordering = ["submission_id", "test_case_id"]
