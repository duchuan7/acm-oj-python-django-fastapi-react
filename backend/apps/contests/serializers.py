from collections import defaultdict

from django.db import transaction
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
        if validated_data["end_at"] <= validated_data["start_at"]:
            raise serializers.ValidationError("Contest end time must be after start time.")
        with transaction.atomic():
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
        start_at = validated_data.get("start_at", instance.start_at)
        end_at = validated_data.get("end_at", instance.end_at)
        if end_at <= start_at:
            raise serializers.ValidationError("Contest end time must be after start time.")
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
    submissions = Submission.objects.filter(
        contest=contest,
        submitted_at__gte=contest.start_at,
        submitted_at__lte=contest.end_at,
    ).select_related("user").order_by("submitted_at", "id")
    by_user = defaultdict(list)
    for submission in submissions:
        by_user[submission.user_id].append(submission)

    rows = []
    for user_id, user_submissions in by_user.items():
        problems = defaultdict(list)
        for submission in user_submissions:
            problems[submission.problem_id].append(submission)
        solved = 0
        score = 0
        total_time = 0
        first_submit = user_submissions[0].submitted_at
        for attempts in problems.values():
            accepted = next((item for item in attempts if item.verdict == Submission.Verdict.ACCEPTED), None)
            if contest.rule == Contest.Rule.ACM:
                if accepted:
                    solved += 1
                    wrong_before = sum(
                        item.verdict == Submission.Verdict.WRONG_ANSWER
                        for item in attempts
                        if item.submitted_at <= accepted.submitted_at
                    )
                    minutes = max(0, int((accepted.submitted_at - contest.start_at).total_seconds() // 60))
                    total_time += minutes + wrong_before * 20
            else:
                best = max((item.score for item in attempts), default=0)
                score += best
                if best:
                    solved += 1
                    total_time += max(0, int((attempts[-1].submitted_at - contest.start_at).total_seconds() // 60))
        rows.append({
            "user_id": user_id,
            "username": user_submissions[0].user.username,
            "solved": solved,
            "score": score,
            "total_time_ms": total_time,
            "first_submit": first_submit,
        })
    rows.sort(key=lambda row: (-row["score"] if contest.rule == Contest.Rule.IOI else -row["solved"], row["total_time_ms"], row["first_submit"]))
    return [
        {
            "rank": index + 1,
            "user_id": row["user_id"],
            "username": row["username"],
            "solved": row["solved"],
            "score": row["score"],
            "total_time_ms": row["total_time_ms"],
        }
        for index, row in enumerate(rows)
    ]
