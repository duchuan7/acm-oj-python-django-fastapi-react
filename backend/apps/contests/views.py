from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.permissions import ReadOnlyOrCoachAdmin

from .models import Contest
from .serializers import ContestSerializer, build_ranklist


class ContestViewSet(viewsets.ModelViewSet):
    serializer_class = ContestSerializer
    permission_classes = [ReadOnlyOrCoachAdmin]

    def get_queryset(self):
        qs = Contest.objects.prefetch_related("contest_problems", "participants").select_related("created_by")
        user = self.request.user
        if user.is_staff or user.role in {"ADMIN", "COACH"}:
            return qs
        return qs.filter(is_public=True)

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def ranklist(self, request, pk=None):
        contest = self.get_object()
        return Response(build_ranklist(contest))
