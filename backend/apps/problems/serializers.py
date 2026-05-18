from django.utils import timezone
from rest_framework import serializers

from .models import Problem, ProblemProposal, TestCase


class TestCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestCase
        fields = ["id", "order", "input_file", "output_file", "score", "is_sample"]


class ProblemSerializer(serializers.ModelSerializer):
    test_cases = TestCaseSerializer(many=True, required=False)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = Problem
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "input_description",
            "output_description",
            "samples",
            "time_limit_ms",
            "memory_limit_mb",
            "is_public",
            "created_by",
            "created_by_username",
            "created_at",
            "updated_at",
            "test_cases",
        ]
        read_only_fields = ["id", "created_by", "created_by_username", "created_at", "updated_at"]

    def create(self, validated_data):
        test_cases = validated_data.pop("test_cases", [])
        problem = Problem.objects.create(created_by=self.context["request"].user, **validated_data)
        for case in test_cases:
            TestCase.objects.create(problem=problem, **case)
        return problem

    def update(self, instance, validated_data):
        test_cases = validated_data.pop("test_cases", None)
        instance = super().update(instance, validated_data)
        if test_cases is not None:
            instance.test_cases.all().delete()
            for case in test_cases:
                TestCase.objects.create(problem=instance, **case)
        return instance


class ProblemProposalSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True)
    reviewed_by_username = serializers.CharField(source="reviewed_by.username", read_only=True)
    approved_problem_title = serializers.CharField(source="approved_problem.title", read_only=True)

    class Meta:
        model = ProblemProposal
        fields = [
            "id",
            "author",
            "author_username",
            "title",
            "slug",
            "description",
            "input_description",
            "output_description",
            "samples",
            "time_limit_ms",
            "memory_limit_mb",
            "standard_language",
            "standard_code",
            "status",
            "review_message",
            "reviewed_by",
            "reviewed_by_username",
            "approved_problem",
            "approved_problem_title",
            "created_at",
            "reviewed_at",
        ]
        read_only_fields = [
            "id",
            "author",
            "author_username",
            "status",
            "review_message",
            "reviewed_by",
            "reviewed_by_username",
            "approved_problem",
            "approved_problem_title",
            "created_at",
            "reviewed_at",
        ]

    def create(self, validated_data):
        return ProblemProposal.objects.create(author=self.context["request"].user, **validated_data)


class ProblemProposalReviewSerializer(serializers.Serializer):
    review_message = serializers.CharField(required=False, allow_blank=True)

    def approve(self, proposal, reviewer):
        if proposal.status != ProblemProposal.Status.PENDING:
            raise serializers.ValidationError("Only pending proposals can be approved.")
        if Problem.objects.filter(slug=proposal.slug).exists():
            raise serializers.ValidationError("A problem with this slug already exists.")
        problem = Problem.objects.create(
            title=proposal.title,
            slug=proposal.slug,
            description=proposal.description,
            input_description=proposal.input_description,
            output_description=proposal.output_description,
            samples=proposal.samples,
            time_limit_ms=proposal.time_limit_ms,
            memory_limit_mb=proposal.memory_limit_mb,
            is_public=True,
            created_by=proposal.author,
        )
        proposal.status = ProblemProposal.Status.APPROVED
        proposal.reviewed_by = reviewer
        proposal.reviewed_at = timezone.now()
        proposal.review_message = self.validated_data.get("review_message", "")
        proposal.approved_problem = problem
        proposal.save()
        return proposal

    def reject(self, proposal, reviewer):
        if proposal.status != ProblemProposal.Status.PENDING:
            raise serializers.ValidationError("Only pending proposals can be rejected.")
        proposal.status = ProblemProposal.Status.REJECTED
        proposal.reviewed_by = reviewer
        proposal.reviewed_at = timezone.now()
        proposal.review_message = self.validated_data.get("review_message", "")
        proposal.save()
        return proposal
