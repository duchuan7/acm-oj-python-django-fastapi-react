from django.conf import settings
from django.db import models


class Contest(models.Model):
    class Rule(models.TextChoices):
        ACM = "ACM", "ACM"
        IOI = "IOI", "IOI"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    rule = models.CharField(max_length=8, choices=Rule.choices, default=Rule.ACM)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    is_public = models.BooleanField(default=False)
    freeze_rank_minutes = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="contests", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_at"]


class ContestProblem(models.Model):
    contest = models.ForeignKey(Contest, related_name="contest_problems", on_delete=models.CASCADE)
    problem = models.ForeignKey("problems.Problem", on_delete=models.PROTECT)
    alias = models.CharField(max_length=8, help_text="A/B/C...")
    score = models.PositiveIntegerField(default=100)
    order = models.PositiveIntegerField()
    created_for_contest = models.BooleanField(default=False)

    class Meta:
        unique_together = [("contest", "problem"), ("contest", "alias")]
        ordering = ["contest_id", "order"]


class ContestRankSnapshot(models.Model):
    contest = models.ForeignKey(Contest, related_name="rank_snapshots", on_delete=models.CASCADE)
    generated_at = models.DateTimeField(auto_now_add=True)
    frozen = models.BooleanField(default=False)
    payload = models.JSONField(default=dict)
