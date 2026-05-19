from django.contrib import admin

from .models import Submission, SubmissionCaseResult


class SubmissionCaseResultInline(admin.TabularInline):
    model = SubmissionCaseResult
    extra = 0
    readonly_fields = ("case", "status", "time_used", "memory_used", "exit_code", "score", "message")


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "problem", "language", "verdict", "score", "submitted_at", "judged_at")
    list_filter = ("language", "verdict")
    inlines = [SubmissionCaseResultInline]
