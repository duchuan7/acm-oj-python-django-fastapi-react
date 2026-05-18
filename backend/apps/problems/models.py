from django.conf import settings
from django.db import models


class Problem(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField()
    input_description = models.TextField()
    output_description = models.TextField()
    samples = models.JSONField(default=list, help_text="[{input: str, output: str}]")
    time_limit_ms = models.PositiveIntegerField(default=1000)
    memory_limit_mb = models.PositiveIntegerField(default=256)
    is_public = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.id}. {self.title}"


class ProblemProposal(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="problem_proposals", on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220)
    description = models.TextField()
    input_description = models.TextField()
    output_description = models.TextField()
    samples = models.JSONField(default=list, help_text="[{input: str, output: str}]")
    time_limit_ms = models.PositiveIntegerField(default=1000)
    memory_limit_mb = models.PositiveIntegerField(default=256)
    standard_language = models.CharField(max_length=16, default="CPP")
    standard_code = models.TextField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    review_message = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="reviewed_problem_proposals",
        on_delete=models.SET_NULL,
    )
    approved_problem = models.ForeignKey(Problem, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]


class TestCase(models.Model):
    problem = models.ForeignKey(Problem, related_name="test_cases", on_delete=models.CASCADE)
    order = models.PositiveIntegerField()
    input_file = models.CharField(max_length=512)
    output_file = models.CharField(max_length=512)
    score = models.PositiveIntegerField(default=0)
    is_sample = models.BooleanField(default=False)

    class Meta:
        unique_together = [("problem", "order")]
        ordering = ["problem_id", "order"]
