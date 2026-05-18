from django.contrib import admin

from .models import Problem, ProblemProposal, TestCase


class TestCaseInline(admin.TabularInline):
    model = TestCase
    extra = 1


@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "is_public", "time_limit_ms", "memory_limit_mb")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [TestCaseInline]


@admin.register(ProblemProposal)
class ProblemProposalAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "author", "status", "created_at", "reviewed_at")
    list_filter = ("status",)
    search_fields = ("title", "author__username", "description")
    readonly_fields = ("created_at", "reviewed_at")
