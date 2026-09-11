from django.db.models import Count, Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from apps.common.permissions import IsAdminRole, IsCoachOrAdmin, ReadOnlyOrCoachAdmin
from apps.submissions.models import Submission

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
        queryset = (
            Problem.objects.prefetch_related("test_cases")
            .select_related("created_by")
            .annotate(
                submission_count=Count("submission", distinct=True),
                accepted_count=Count(
                    "submission",
                    filter=Q(submission__verdict=Submission.Verdict.ACCEPTED),
                    distinct=True,
                ),
            )
        )
        search = self.request.query_params.get("search")
        tag = self.request.query_params.get("tag")
        difficulty_min = self.request.query_params.get("difficulty_min")
        difficulty_max = self.request.query_params.get("difficulty_max")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(slug__icontains=search)
                | Q(source__icontains=search)
            )
        if tag:
            queryset = queryset.filter(tags__contains=[tag])
        if difficulty_min:
            queryset = queryset.filter(difficulty__gte=difficulty_min)
        if difficulty_max:
            queryset = queryset.filter(difficulty__lte=difficulty_max)
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
            return [IsAdminRole()]
        return [IsAuthenticated()]

    def perform_update(self, serializer):
        user = self.request.user
        instance = serializer.instance
        if not (user.is_staff or user.role == "ADMIN" or instance.author_id == user.id):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("You can only edit your own proposals.")
        if not (user.is_staff or user.role == "ADMIN") and instance.status != ProblemProposal.Status.PENDING:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Only pending proposals can be edited.")
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if not (user.is_staff or user.role == "ADMIN" or instance.author_id == user.id):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("You can only delete your own proposals.")
        instance.delete()

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
            return [IsAdminRole()]
        return [IsAuthenticatedOrReadOnly()]

    def perform_update(self, serializer):
        user = self.request.user
        instance = serializer.instance
        if not (user.is_staff or user.role == "ADMIN" or instance.author_id == user.id):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("You can only edit your own solutions.")
        if user.id == instance.author_id and not (user.is_staff or user.role == "ADMIN"):
            serializer.save(
                status=ProblemSolution.Status.PENDING,
                reviewed_by=None,
                reviewed_at=None,
                review_message="",
            )
        else:
            serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if not (user.is_staff or user.role == "ADMIN" or instance.author_id == user.id):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("You can only delete your own solutions.")
        instance.delete()

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
