from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from apps.common.permissions import IsCoachOrAdmin, ReadOnlyOrCoachAdmin

from .models import Problem, ProblemProposal, ProblemSolution
from .serializers import (
    ProblemProposalReviewSerializer,
    ProblemProposalSerializer,
    ProblemSerializer,
    ProblemSolutionReviewSerializer,
    ProblemSolutionSerializer,
)


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


class ProblemSolutionViewSet(viewsets.ModelViewSet):
    serializer_class = ProblemSolutionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = ProblemSolution.objects.select_related("problem", "author", "reviewed_by")
        problem_id = self.request.query_params.get("problem")
        status_value = self.request.query_params.get("status")
        if problem_id:
            queryset = queryset.filter(problem_id=problem_id)
        if status_value:
            queryset = queryset.filter(status=status_value)
        user = self.request.user
        if not user.is_authenticated:
            return queryset.filter(status=ProblemSolution.Status.APPROVED)
        if user.is_staff or user.role in {"ADMIN", "COACH"}:
            return queryset
        return (
            queryset.filter(status=ProblemSolution.Status.APPROVED)
            | queryset.filter(author=user)
        ).distinct()

    def get_permissions(self):
        if self.action in {"approve", "reject"}:
            return [IsCoachOrAdmin()]
        return [IsAuthenticatedOrReadOnly()]

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        solution = self.get_object()
        serializer = ProblemSolutionReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        solution = serializer.approve(solution, request.user)
        return Response(ProblemSolutionSerializer(solution).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        solution = self.get_object()
        serializer = ProblemSolutionReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        solution = serializer.reject(solution, request.user)
        return Response(ProblemSolutionSerializer(solution).data)
