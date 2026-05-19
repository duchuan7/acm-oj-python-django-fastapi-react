from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.problems.models import Problem

from .models import Contest
from .serializers import ContestSerializer, build_ranklist


class ContestPermission(IsAuthenticated):
    def has_permission(self, request, view):
        if request.method in {"GET", "HEAD", "OPTIONS"}:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in {"GET", "HEAD", "OPTIONS"}:
            return True
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.is_staff or user.role in {"ADMIN", "COACH"} or obj.created_by_id == user.id


def publish_finished_contest_problems():
    problem_ids = Contest.objects.filter(
        end_at__lte=timezone.now(),
        contest_problems__created_for_contest=True,
        contest_problems__problem__is_public=False,
    ).values_list("contest_problems__problem_id", flat=True)
    Problem.objects.filter(id__in=problem_ids).update(is_public=True)


class ContestViewSet(viewsets.ModelViewSet):
    serializer_class = ContestSerializer
    permission_classes = [ContestPermission]

    def get_queryset(self):
        publish_finished_contest_problems()
        qs = Contest.objects.prefetch_related("contest_problems", "participants").select_related("created_by")
        user = self.request.user
        visibility = self.request.query_params.get("visibility")
        if visibility == "public":
            qs = qs.filter(is_public=True)
        elif visibility == "private":
            qs = qs.filter(is_public=False)

        if user.is_authenticated and (user.is_staff or user.role in {"ADMIN", "COACH"}):
            return qs
        if user.is_authenticated:
            return qs.filter(Q(is_public=True) | Q(created_by=user) | Q(participants=user)).distinct()
        return qs.filter(is_public=True)

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def ranklist(self, request, pk=None):
        publish_finished_contest_problems()
        contest = self.get_object()
        return Response(build_ranklist(contest))
