from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers as drf_serializers
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordResetForm

from assessments.models import AssessmentSession
from frontend.models import LeadInquiry

from .serializers import (
    AssessmentSessionDetailSerializer,
    AssessmentSessionListSerializer,
    AthleteSerializer,
    EnrollmentSerializer,
    LeadInquirySerializer,
)


_Detail = inline_serializer("Detail", {"detail": drf_serializers.CharField()})


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=inline_serializer("LoginRequest", {"username": drf_serializers.CharField(), "password": drf_serializers.CharField()}),
        responses={200: inline_serializer("LoginResponse", {"access": drf_serializers.CharField(), "refresh": drf_serializers.CharField(), "athlete_id": drf_serializers.IntegerField(allow_null=True), "full_name": drf_serializers.CharField()}), 400: _Detail, 401: _Detail},
    )
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


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=inline_serializer("ForgotPasswordRequest", {"email": drf_serializers.EmailField()}),
        responses={200: _Detail, 400: _Detail},
    )
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
    # No access token required: holding the refresh token is the proof, and logout
    # must still work after the access token has expired.
    permission_classes = [AllowAny]

    @extend_schema(
        request=inline_serializer("LogoutRequest", {"refresh": drf_serializers.CharField(required=False)}),
        responses={204: OpenApiResponse(description="No content")},
    )
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

    @extend_schema(responses={200: AthleteSerializer, 404: _Detail})
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

    @extend_schema(
        responses={
            200: inline_serializer(
                "Dashboard",
                {
                    "athlete": AthleteSerializer(),
                    "primary_enrollment": EnrollmentSerializer(allow_null=True),
                    "recent_sessions": AssessmentSessionListSerializer(many=True),
                },
            ),
            404: _Detail,
        }
    )
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
            AssessmentSession.objects.visible_to_athlete()
            .filter(athlete=athlete)
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

    @extend_schema(responses={200: AssessmentSessionListSerializer(many=True), 404: _Detail})
    def get(self, request):
        athlete = getattr(request.user, "athlete_profile", None)
        if not athlete:
            return Response(
                {"detail": "No athlete profile linked to this account."},
                status=status.HTTP_404_NOT_FOUND,
            )

        sessions = (
            AssessmentSession.objects.visible_to_athlete()
            .filter(athlete=athlete)
            .select_related("protocol", "protocol__framework", "protocol__framework__domain")
            .order_by("-assessed_on")
        )
        return Response(AssessmentSessionListSerializer(sessions, many=True).data)


class AthleteSessionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: AssessmentSessionDetailSerializer, 404: _Detail})
    def get(self, request, session_id):
        athlete = getattr(request.user, "athlete_profile", None)
        if not athlete:
            return Response(
                {"detail": "No athlete profile linked to this account."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            session = AssessmentSession.objects.visible_to_athlete().select_related(
                "protocol",
                "protocol__framework",
                "protocol__framework__domain",
                "sport",
            ).get(id=session_id, athlete=athlete)
        except AssessmentSession.DoesNotExist:
            return Response({"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(AssessmentSessionDetailSerializer(session).data)


# ── Lead Inquiry ──────────────────────────────────────────────────────────────

class LeadInquiryCreateView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=LeadInquirySerializer,
        responses={201: _Detail, 400: OpenApiResponse(description="Field errors: {field: [messages]}")},
    )
    def post(self, request):
        serializer = LeadInquirySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(metadata={"source": "mobile_app"})
            return Response(
                {"detail": "Your enquiry has been received. Our team will be in touch shortly."},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
