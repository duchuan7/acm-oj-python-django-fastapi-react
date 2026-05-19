from django.conf import settings
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.permissions import IsCoachOrAdmin

from .models import Submission, SubmissionCaseResult
from .serializers import JudgePayloadSerializer, JudgeResultSerializer, SubmissionSerializer


class SubmissionViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = SubmissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Submission.objects.select_related("user", "problem", "contest").prefetch_related("case_results")
        user = self.request.user
        problem = self.request.query_params.get("problem")
        if user.is_staff or user.role in {"ADMIN", "COACH"}:
            scoped = qs
        elif problem:
            scoped = qs
        else:
            scoped = qs.filter(user=user)

        language = self.request.query_params.get("language")
        status_value = self.request.query_params.get("status") or self.request.query_params.get("verdict")
        if problem:
            scoped = scoped.filter(problem_id=problem)
        if language:
            scoped = scoped.filter(language=language)
        if status_value:
            scoped = scoped.filter(verdict=status_value)
        return scoped


class InternalJudgeViewSet(viewsets.GenericViewSet):
    queryset = Submission.objects.select_related("problem", "contest")

    def _check_token(self, request):
        return request.headers.get("X-Judge-Token") == settings.JUDGE_INTERNAL_TOKEN

    def get_permissions(self):
        return []

    @action(detail=True, methods=["get"], url_path="payload")
    def payload(self, request, pk=None):
        if not self._check_token(request):
            return Response({"detail": "Invalid judge token."}, status=status.HTTP_403_FORBIDDEN)
        submission = self.get_object()
        submission.verdict = Submission.Verdict.JUDGING
        submission.save(update_fields=["verdict"])
        return Response(JudgePayloadSerializer(submission).data)

    @action(detail=True, methods=["post"], url_path="result")
    def result(self, request, pk=None):
        if not self._check_token(request):
            return Response({"detail": "Invalid judge token."}, status=status.HTTP_403_FORBIDDEN)
        submission = self.get_object()
        serializer = JudgeResultSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        SubmissionCaseResult.objects.filter(submission=submission).delete()
        submission.verdict = data["verdict"]
        submission.score = data.get("score", 0)
        submission.max_time_ms = data.get("max_time_ms", 0)
        submission.max_memory_kb = data.get("max_memory_kb", 0)
        submission.compile_message = data.get("compile_message", "")
        submission.judged_at = timezone.now()
        submission.save()

        for item in data.get("case_results", []):
            SubmissionCaseResult.objects.create(
                submission=submission,
                case_id=item["test_case_id"],
                status=item.get("status") or item["verdict"],
                time_used=item.get("time_used", item.get("time_ms", 0)),
                memory_used=item.get("memory_used", item.get("memory_kb", 0)),
                exit_code=item.get("exit_code"),
                stdout=item.get("stdout", ""),
                stderr=item.get("stderr", ""),
                score=item.get("score", 0),
                message=item.get("message", ""),
            )
        return Response(SubmissionSerializer(submission).data)
