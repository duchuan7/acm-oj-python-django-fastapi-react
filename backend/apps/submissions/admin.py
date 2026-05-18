from django.contrib import admin

from .models import JudgeCaseResult, Submission


class JudgeCaseResultInline(admin.TabularInline):
    model = JudgeCaseResult
    extra = 0
    readonly_fields = ("test_case", "verdict", "time_ms", "memory_kb", "score", "message")


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "problem", "language", "verdict", "score", "submitted_at", "judged_at")
    list_filter = ("language", "verdict")
    inlines = [JudgeCaseResultInline]
