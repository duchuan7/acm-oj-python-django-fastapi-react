from django.contrib import admin
from django.urls import include, path
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter
from rest_framework.views import APIView

from apps.accounts.views import AuthViewSet, UserViewSet
from apps.contests.views import ContestViewSet
from apps.blogs.views import BlogPostViewSet
from apps.problems.views import ProblemProposalViewSet, ProblemSolutionViewSet, ProblemViewSet
from apps.submissions.views import InternalJudgeViewSet, SubmissionViewSet


class ApiRootView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response(
            {
                "name": "duilio OJ",
                "modules": ["accounts", "problems", "problem-proposals", "problem-solutions", "submissions", "contests", "ranklist", "blogs"],
            }
        )


router = DefaultRouter()
router.register("auth", AuthViewSet, basename="auth")
router.register("users", UserViewSet, basename="users")
router.register("problems", ProblemViewSet, basename="problems")
router.register("problem-proposals", ProblemProposalViewSet, basename="problem-proposals")
router.register("problem-solutions", ProblemSolutionViewSet, basename="problem-solutions")
router.register("submissions", SubmissionViewSet, basename="submissions")
router.register("contests", ContestViewSet, basename="contests")
router.register("blogs", BlogPostViewSet, basename="blogs")
router.register("internal/judge", InternalJudgeViewSet, basename="internal-judge")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", ApiRootView.as_view(), name="api-root"),
    path("api/", include(router.urls)),
]
