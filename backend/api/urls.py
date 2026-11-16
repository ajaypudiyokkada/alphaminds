from django.urls import path

from . import views

app_name = "api"

urlpatterns = [
    # Auth
    path("auth/login/", views.LoginView.as_view(), name="login"),
    path("auth/refresh/", views.RefreshView.as_view(), name="token_refresh"),
    path("auth/logout/", views.LogoutView.as_view(), name="logout"),
    path("auth/forgot-password/", views.ForgotPasswordView.as_view(), name="forgot_password"),

    # Athlete
    path("athlete/me/", views.AthleteMeView.as_view(), name="athlete_me"),
    path("athlete/dashboard/", views.AthleteDashboardView.as_view(), name="athlete_dashboard"),
    path("athlete/sessions/", views.AthleteSessionListView.as_view(), name="session_list"),
    path("athlete/sessions/<int:session_id>/", views.AthleteSessionDetailView.as_view(), name="session_detail"),

    # Public
    path("leads/", views.LeadInquiryCreateView.as_view(), name="lead_create"),
]
