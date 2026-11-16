from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordResetForm

from assessments.models import AssessmentSession
from core.choices import AssessmentSessionStatusChoices
from frontend.models import LeadInquiry

from .serializers import (
    AssessmentSessionDetailSerializer,
    AssessmentSessionListSerializer,
    AthleteSerializer,
    EnrollmentSerializer,
    LeadInquirySerializer,
)


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        if not username or not password:
            return Response(
                {"detail": "username and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response(
                {"detail": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)
        athlete = getattr(user, "athlete_profile", None)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "athlete_id": athlete.id if athlete else None,
                "full_name": athlete.full_name if athlete else user.get_full_name(),
            }
        )


class RefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get("refresh")
        if not token:
            return Response(
                {"detail": "refresh token required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            refresh = RefreshToken(token)
            return Response({"access": str(refresh.access_token)})
        except Exception:
            return Response(
                {"detail": "Invalid or expired refresh token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email", "").strip()
        if not email:
            return Response({"detail": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        form = PasswordResetForm({"email": email})
        if form.is_valid():
            form.save(
                request=request,
                use_https=request.is_secure(),
                from_email=None,
                email_template_name="registration/password_reset_email.html",
                subject_template_name="registration/password_reset_subject.txt",
            )
        # Always return success — never reveal whether email exists
        return Response({"detail": "If an account is linked to this email, a reset link has been sent."})


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = request.data.get("refresh")
        if token:
            try:
                RefreshToken(token).blacklist()
            except Exception:
                pass
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Athlete ───────────────────────────────────────────────────────────────────

class AthleteMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        athlete = getattr(request.user, "athlete_profile", None)
        if not athlete:
            return Response(
                {"detail": "No athlete profile linked to this account."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(AthleteSerializer(athlete).data)


class AthleteDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        athlete = getattr(request.user, "athlete_profile", None)
        if not athlete:
            return Response(
                {"detail": "No athlete profile linked to this account."},
                status=status.HTTP_404_NOT_FOUND,
            )

        primary_enrollment = (
            athlete.enrollments.filter(is_active=True, status="active")
            .select_related("center", "sport")
            .order_by("-start_date", "-id")
            .first()
        )

        recent_sessions = (
            AssessmentSession.objects.filter(
                athlete=athlete,
                status=AssessmentSessionStatusChoices.PUBLISHED,
                is_active=True,
            )
            .select_related("protocol", "protocol__framework", "protocol__framework__domain")
            .order_by("-assessed_on")[:5]
        )

        return Response(
            {
                "athlete": AthleteSerializer(athlete).data,
                "primary_enrollment": EnrollmentSerializer(primary_enrollment).data if primary_enrollment else None,
                "recent_sessions": AssessmentSessionListSerializer(recent_sessions, many=True).data,
            }
        )


# ── Sessions ──────────────────────────────────────────────────────────────────

class AthleteSessionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        athlete = getattr(request.user, "athlete_profile", None)
        if not athlete:
            return Response(
                {"detail": "No athlete profile linked to this account."},
                status=status.HTTP_404_NOT_FOUND,
            )

        sessions = (
            AssessmentSession.objects.filter(athlete=athlete, is_active=True)
            .select_related("protocol", "protocol__framework", "protocol__framework__domain")
            .order_by("-assessed_on")
        )
        return Response(AssessmentSessionListSerializer(sessions, many=True).data)


class AthleteSessionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        athlete = getattr(request.user, "athlete_profile", None)
        if not athlete:
            return Response(
                {"detail": "No athlete profile linked to this account."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            session = AssessmentSession.objects.select_related(
                "protocol",
                "protocol__framework",
                "protocol__framework__domain",
                "sport",
            ).get(id=session_id, athlete=athlete, is_active=True)
        except AssessmentSession.DoesNotExist:
            return Response({"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(AssessmentSessionDetailSerializer(session).data)


# ── Lead Inquiry ──────────────────────────────────────────────────────────────

class LeadInquiryCreateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LeadInquirySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(metadata={"source": "mobile_app"})
            return Response(
                {"detail": "Your enquiry has been received. Our team will be in touch shortly."},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
