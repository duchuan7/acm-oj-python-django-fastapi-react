from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.conf import settings
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.common.permissions import IsAdminRole
from apps.blogs.models import BlogPost
from apps.submissions.models import Submission

from .authentication import LastSeenTokenAuthentication
from .serializers import (
    BlogProfileSerializer,
    LoginSerializer,
    PasswordResetRequestSerializer,
    PublicUserSerializer,
    RegistrationCodeRequestSerializer,
    RegisterSerializer,
    SubmissionProfileSerializer,
    UserSerializer,
)
from .verification import send_registration_code

User = get_user_model()


class AuthViewSet(viewsets.GenericViewSet):
    authentication_classes = [LastSeenTokenAuthentication]
    permission_classes = [AllowAny]

    @action(detail=False, methods=["post"], serializer_class=RegisterSerializer)
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user.last_seen_at = timezone.now()
        user.save(update_fields=["last_seen_at"])
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user": UserSerializer(user).data}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], serializer_class=RegistrationCodeRequestSerializer)
    def registration_code(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        remote_addr = request.META.get("REMOTE_ADDR", "unknown")
        trusted_proxies = {value.strip() for value in settings.REGISTRATION_TRUSTED_PROXIES.split(",") if value.strip()}
        if remote_addr in trusted_proxies:
            forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
            ip_address = forwarded_for.split(",")[0].strip() if forwarded_for else remote_addr
        else:
            ip_address = remote_addr
        send_registration_code(serializer.validated_data["email"], ip_address)
        return Response({"detail": "Verification code sent."})

    @action(detail=False, methods=["post"], serializer_class=LoginSerializer)
    def login(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        user.last_seen_at = timezone.now()
        user.save(update_fields=["last_seen_at"])
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user": UserSerializer(user).data})

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        return Response(UserSerializer(request.user).data)

    @action(detail=False, methods=["post"], serializer_class=PasswordResetRequestSerializer)
    def password_reset(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"detail": "Password reset email hook accepted. Configure SMTP to send real mail."})


class UserViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.all().order_by("id")
    serializer_class = UserSerializer

    def get_serializer_class(self):
        if self.action in {"list", "retrieve"}:
            return PublicUserSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        if self.action in {"profile", "leaderboard"}:
            return [AllowAny()]
        if self.action in {"list", "retrieve"}:
            return [IsAuthenticated()]
        return [IsAdminRole()]

    @action(detail=False, methods=["get"])
    def leaderboard(self, request):
        rows = (
            User.objects.annotate(
                solved_count=Count(
                    "submission__problem_id",
                    filter=Q(submission__verdict=Submission.Verdict.ACCEPTED),
                    distinct=True,
                ),
                submission_count=Count("submission", distinct=True),
            )
            .filter(submission_count__gt=0)
            .order_by("-solved_count", "submission_count", "username")[:10]
        )
        return Response(
            [
                {
                    "rank": index + 1,
                    "user_id": user.id,
                    "username": user.username,
                    "solved_count": user.solved_count,
                    "submission_count": user.submission_count,
                }
                for index, user in enumerate(rows)
            ]
        )

    @action(detail=True, methods=["get"])
    def profile(self, request, pk=None):
        user = self.get_object()
        viewer = request.user
        submissions = Submission.objects.filter(user=user).select_related("problem")[:30]
        blogs = BlogPost.objects.filter(author=user).order_by("-created_at")
        solved_count = (
            Submission.objects.filter(user=user, verdict=Submission.Verdict.ACCEPTED)
            .values("problem_id")
            .distinct()
            .count()
        )
        submission_count = Submission.objects.filter(user=user).count()
        if not (
            viewer.is_authenticated
            and (viewer.is_staff or getattr(viewer, "role", None) in {"ADMIN", "COACH"} or viewer.id == user.id)
        ):
            blogs = blogs.filter(status=BlogPost.Status.PUBLISHED)
        return Response(
            {
                "user": PublicUserSerializer(user).data,
                "stats": {
                    "solved_count": solved_count,
                    "submission_count": submission_count,
                },
                "submissions": SubmissionProfileSerializer(submissions, many=True).data,
                "blogs": BlogProfileSerializer(blogs[:30], many=True).data,
            }
        )
