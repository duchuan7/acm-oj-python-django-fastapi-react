from django.db.models import Count, Min, Q, Sum
from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.submissions.models import Submission

from .models import Contest, ContestProblem

User = get_user_model()


class ContestProblemSerializer(serializers.ModelSerializer):
    problem_title = serializers.CharField(source="problem.title", read_only=True)

    class Meta:
        model = ContestProblem
        fields = ["id", "problem", "problem_title", "alias", "score", "order"]


class ContestSerializer(serializers.ModelSerializer):
    contest_problems = ContestProblemSerializer(many=True, required=False)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)
    participants = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        required=False,
    )

    class Meta:
        model = Contest
        fields = [
            "id",
            "title",
            "description",
            "rule",
            "start_at",
            "end_at",
            "is_public",
            "freeze_rank_minutes",
            "created_by",
            "created_by_username",
            "participants",
            "contest_problems",
            "created_at",
        ]
        read_only_fields = ["id", "created_by", "created_by_username", "created_at"]

    def create(self, validated_data):
        problems = validated_data.pop("contest_problems", [])
        participants = validated_data.pop("participants", [])
        contest = Contest.objects.create(created_by=self.context["request"].user, **validated_data)
        contest.participants.set(participants)
        for item in problems:
            ContestProblem.objects.create(contest=contest, **item)
        return contest

    def update(self, instance, validated_data):
        problems = validated_data.pop("contest_problems", None)
        participants = validated_data.pop("participants", None)
        instance = super().update(instance, validated_data)
        if participants is not None:
            instance.participants.set(participants)
        if problems is not None:
            instance.contest_problems.all().delete()
            for item in problems:
                ContestProblem.objects.create(contest=instance, **item)
        return instance


def build_ranklist(contest):
    rows = (
        Submission.objects.filter(contest=contest)
        .values("user_id", "user__username")
        .annotate(
            solved=Count("problem_id", filter=Q(verdict=Submission.Verdict.AC), distinct=True),
            score=Sum("score"),
            total_time=Sum("max_time_ms"),
            first_submit=Min("submitted_at"),
        )
        .order_by("-solved", "total_time", "first_submit")
    )
    return [
        {
            "rank": index + 1,
            "user_id": row["user_id"],
            "username": row["user__username"],
            "solved": row["solved"] or 0,
            "score": row["score"] or 0,
            "total_time_ms": row["total_time"] or 0,
        }
        for index, row in enumerate(rows)
    ]
