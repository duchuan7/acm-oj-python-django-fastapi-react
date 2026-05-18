from django.contrib.auth import get_user_model
from rest_framework import mixins, status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.common.permissions import IsAdminRole
from apps.blogs.models import BlogPost
from apps.submissions.models import Submission

from .serializers import (
    BlogProfileSerializer,
    LoginSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    SubmissionProfileSerializer,
    UserSerializer,
)

User = get_user_model()


class AuthViewSet(viewsets.GenericViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    @action(detail=False, methods=["post"], serializer_class=RegisterSerializer)
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user": UserSerializer(user).data}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], serializer_class=LoginSerializer)
    def login(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
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

    def get_permissions(self):
        if self.action in {"list", "retrieve", "profile"}:
            return [IsAuthenticated()]
        return [IsAdminRole()]

    @action(detail=True, methods=["get"])
    def profile(self, request, pk=None):
        user = self.get_object()
        viewer = request.user
        submissions = Submission.objects.filter(user=user).select_related("problem")[:30]
        blogs = BlogPost.objects.filter(author=user).order_by("-created_at")
        if not (viewer.is_staff or viewer.role in {"ADMIN", "COACH"} or viewer.id == user.id):
            blogs = blogs.filter(status=BlogPost.Status.PUBLISHED)
        return Response(
            {
                "user": UserSerializer(user).data,
                "submissions": SubmissionProfileSerializer(submissions, many=True).data,
                "blogs": BlogProfileSerializer(blogs[:30], many=True).data,
            }
        )
