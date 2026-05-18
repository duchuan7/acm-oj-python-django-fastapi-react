from django.conf import settings
from django.utils import timezone
from rest_framework import serializers

from apps.problems.models import TestCase

from .models import JudgeCaseResult, Submission
from .queue import enqueue_submission


def testcase_path(path):
    if path.startswith("/"):
        return path
    return f"/data/testcases/{path}"


class JudgeCaseResultSerializer(serializers.ModelSerializer):
    test_case_order = serializers.IntegerField(source="test_case.order", read_only=True)

    class Meta:
        model = JudgeCaseResult
        fields = ["id", "test_case", "test_case_order", "verdict", "time_ms", "memory_kb", "score", "message"]


class SubmissionSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    problem_title = serializers.CharField(source="problem.title", read_only=True)
    case_results = JudgeCaseResultSerializer(many=True, read_only=True)

    class Meta:
        model = Submission
        fields = [
            "id",
            "user",
            "username",
            "problem",
            "problem_title",
            "contest",
            "language",
            "code",
            "code_size",
            "verdict",
            "score",
            "max_time_ms",
            "max_memory_kb",
            "compile_message",
            "submitted_at",
            "judged_at",
            "case_results",
        ]
        read_only_fields = [
            "id",
            "user",
            "code_size",
            "verdict",
            "score",
            "max_time_ms",
            "max_memory_kb",
            "compile_message",
            "submitted_at",
            "judged_at",
            "case_results",
        ]

    def validate_code(self, value):
        size = len(value.encode("utf-8"))
        if size > settings.SUBMISSION_CODE_MAX_BYTES:
            raise serializers.ValidationError(f"Code size must be <= {settings.SUBMISSION_CODE_MAX_BYTES} bytes.")
        return value

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user
        last = (
            Submission.objects.filter(user=user)
            .order_by("-submitted_at")
            .values_list("submitted_at", flat=True)
            .first()
        )
        if last:
            elapsed = (timezone.now() - last).total_seconds()
            if elapsed < settings.SUBMISSION_RATE_LIMIT_SECONDS:
                raise serializers.ValidationError("Submit too frequently. Please wait before submitting again.")
        return attrs

    def create(self, validated_data):
        code = validated_data["code"]
        submission = Submission.objects.create(
            user=self.context["request"].user,
            code_size=len(code.encode("utf-8")),
            **validated_data,
        )
        enqueue_submission(submission.id)
        return submission


class JudgePayloadSerializer(serializers.ModelSerializer):
    time_limit_ms = serializers.IntegerField(source="problem.time_limit_ms")
    memory_limit_mb = serializers.IntegerField(source="problem.memory_limit_mb")
    contest_rule = serializers.CharField(source="contest.rule", allow_null=True)
    test_cases = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = [
            "id",
            "language",
            "code",
            "time_limit_ms",
            "memory_limit_mb",
            "contest_rule",
            "test_cases",
        ]

    def get_test_cases(self, obj):
        qs = TestCase.objects.filter(problem=obj.problem).order_by("order")
        return [
            {
                "id": case.id,
                "order": case.order,
                "input_file": testcase_path(case.input_file),
                "output_file": testcase_path(case.output_file),
                "score": case.score,
            }
            for case in qs
        ]


class JudgeResultSerializer(serializers.Serializer):
    verdict = serializers.ChoiceField(choices=Submission.Verdict.choices)
    score = serializers.IntegerField(min_value=0, default=0)
    max_time_ms = serializers.IntegerField(min_value=0, default=0)
    max_memory_kb = serializers.IntegerField(min_value=0, default=0)
    compile_message = serializers.CharField(required=False, allow_blank=True)
    case_results = serializers.ListField(child=serializers.DictField(), required=False)
