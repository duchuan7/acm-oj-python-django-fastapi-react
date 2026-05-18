from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.permissions import IsCoachOrAdmin, ReadOnlyOrCoachAdmin

from .models import Problem, ProblemProposal
from .serializers import ProblemProposalReviewSerializer, ProblemProposalSerializer, ProblemSerializer


class ProblemViewSet(viewsets.ModelViewSet):
    serializer_class = ProblemSerializer
    permission_classes = [ReadOnlyOrCoachAdmin]

    def get_queryset(self):
        queryset = Problem.objects.prefetch_related("test_cases").select_related("created_by")
        user = self.request.user
        if user.is_staff or getattr(user, "role", None) in {"ADMIN", "COACH"}:
            return queryset
        return queryset.filter(is_public=True)


class ProblemProposalViewSet(viewsets.ModelViewSet):
    serializer_class = ProblemProposalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = ProblemProposal.objects.select_related("author", "reviewed_by", "approved_problem")
        user = self.request.user
        if user.is_staff or user.role in {"ADMIN", "COACH"}:
            return queryset
        return queryset.filter(author=user)

    def get_permissions(self):
        if self.action in {"approve", "reject"}:
            return [IsCoachOrAdmin()]
        return [IsAuthenticated()]

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        proposal = self.get_object()
        serializer = ProblemProposalReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        proposal = serializer.approve(proposal, request.user)
        return Response(ProblemProposalSerializer(proposal).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        proposal = self.get_object()
        serializer = ProblemProposalReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        proposal = serializer.reject(proposal, request.user)
        return Response(ProblemProposalSerializer(proposal).data)
