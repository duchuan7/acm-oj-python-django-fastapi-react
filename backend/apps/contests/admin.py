from django.contrib import admin

from .models import Contest, ContestProblem, ContestRankSnapshot


class ContestProblemInline(admin.TabularInline):
    model = ContestProblem
    extra = 1
    fields = ("alias", "problem", "score", "order", "created_for_contest")


@admin.register(Contest)
class ContestAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "rule", "start_at", "end_at", "is_public", "created_by")
    inlines = [ContestProblemInline]


@admin.register(ContestRankSnapshot)
class ContestRankSnapshotAdmin(admin.ModelAdmin):
    list_display = ("contest", "generated_at", "frozen")
