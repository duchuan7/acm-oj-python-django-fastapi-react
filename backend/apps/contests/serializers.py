from django.db.models import Count, Min, Q, Sum
from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.problems.models import Problem
from apps.problems.serializers import ProblemSerializer
from apps.submissions.models import Submission

from .models import Contest, ContestProblem

User = get_user_model()


class ContestProblemSerializer(serializers.ModelSerializer):
    problem_title = serializers.CharField(source="problem.title", read_only=True)
    problem_detail = ProblemSerializer(source="problem", read_only=True)
    new_problem = serializers.DictField(write_only=True, required=False)

    class Meta:
        model = ContestProblem
        fields = [
            "id",
            "problem",
            "problem_title",
            "problem_detail",
            "new_problem",
            "alias",
            "score",
            "order",
            "created_for_contest",
        ]
        read_only_fields = ["id", "problem_title", "problem_detail", "created_for_contest"]
        extra_kwargs = {"problem": {"required": False, "allow_null": True}}


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
        request = self.context["request"]
        user = request.user
        if validated_data.get("is_public") and not (user.is_staff or user.role == "ADMIN"):
            raise serializers.ValidationError("Only admins can create public contests.")
        contest = Contest.objects.create(created_by=user, **validated_data)
        contest.participants.set(participants)
        for item in problems:
            self._create_contest_problem(contest, item)
        return contest

    def update(self, instance, validated_data):
        problems = validated_data.pop("contest_problems", None)
        participants = validated_data.pop("participants", None)
        request = self.context["request"]
        user = request.user
        if "is_public" in validated_data and validated_data["is_public"] and not (user.is_staff or user.role == "ADMIN"):
            raise serializers.ValidationError("Only admins can make contests public.")
        instance = super().update(instance, validated_data)
        if participants is not None:
            instance.participants.set(participants)
        if problems is not None:
            instance.contest_problems.all().delete()
            for item in problems:
                self._create_contest_problem(instance, item)
        return instance

    def _create_contest_problem(self, contest, item):
        new_problem = item.pop("new_problem", None)
        created_for_contest = False
        if new_problem:
            problem = Problem.objects.create(
                title=new_problem["title"],
                slug=new_problem["slug"],
                description=new_problem["description"],
                input_description=new_problem["input_description"],
                output_description=new_problem["output_description"],
                samples=new_problem.get("samples", []),
                time_limit_ms=new_problem.get("time_limit_ms", 1000),
                memory_limit_mb=new_problem.get("memory_limit_mb", 256),
                is_public=False,
                created_by=self.context["request"].user,
            )
            item["problem"] = problem
            created_for_contest = True
        if not item.get("problem"):
            raise serializers.ValidationError("Each contest problem needs either problem or new_problem.")
        return ContestProblem.objects.create(
            contest=contest,
            created_for_contest=created_for_contest,
            **item,
        )


def build_ranklist(contest):
    rows = (
        Submission.objects.filter(contest=contest)
        .values("user_id", "user__username")
        .annotate(
            solved=Count("problem_id", filter=Q(verdict=Submission.Verdict.ACCEPTED), distinct=True),
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
