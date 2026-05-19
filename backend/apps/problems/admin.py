from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils import timezone

from .models import Problem, ProblemProposal, ProblemSolution, TestCase


class TestCaseInline(admin.TabularInline):
    model = TestCase
    extra = 1


@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "is_public", "time_limit_ms", "memory_limit_mb", "delete_link")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [TestCaseInline]
    actions = ["delete_selected"]

    @admin.display(description="Delete")
    def delete_link(self, obj):
        url = reverse("admin:problems_problem_delete", args=[obj.pk])
        return format_html('<a class="deletelink" href="{}">Delete</a>', url)


@admin.register(ProblemProposal)
class ProblemProposalAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "author", "status", "created_at", "reviewed_at")
    list_filter = ("status",)
    search_fields = ("title", "author__username", "description")
    readonly_fields = ("created_at", "reviewed_at")
    actions = ["reject_selected"]

    @admin.action(description="Reject selected proposals")
    def reject_selected(self, request, queryset):
        queryset.filter(status=ProblemProposal.Status.PENDING).update(
            status=ProblemProposal.Status.REJECTED,
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )


@admin.register(ProblemSolution)
class ProblemSolutionAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "problem", "author", "status", "created_at", "reviewed_at")
    list_filter = ("status", "problem")
    search_fields = ("title", "content", "problem__title", "author__username")
    readonly_fields = ("created_at", "updated_at", "reviewed_at")
    actions = ["approve_selected", "reject_selected"]

    @admin.action(description="Approve selected editorials")
    def approve_selected(self, request, queryset):
        queryset.filter(status=ProblemSolution.Status.PENDING).update(
            status=ProblemSolution.Status.APPROVED,
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )

    @admin.action(description="Reject selected editorials")
    def reject_selected(self, request, queryset):
        queryset.filter(status=ProblemSolution.Status.PENDING).update(
            status=ProblemSolution.Status.REJECTED,
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )
