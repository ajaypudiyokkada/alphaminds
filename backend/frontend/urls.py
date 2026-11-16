from django.urls import path

from . import views

app_name = "frontend"

urlpatterns = [
    path("", views.home_view, name="home"),
    path("dashboard/", views.role_router_view, name="role_router"),
    path("athlete/home/", views.athlete_home_view, name="athlete_home"),
    path("staff/home/", views.staff_home_view, name="staff_home"),
    path("staff/athletes/create/", views.staff_athlete_create_view, name="staff_athlete_create"),
    path("staff/athletes/<int:athlete_id>/", views.staff_athlete_detail_view, name="staff_athlete_detail"),
    path("staff/athletes/<int:athlete_id>/edit/", views.staff_athlete_update_view, name="staff_athlete_update"),
    path("staff/athletes/<int:athlete_id>/delete/", views.staff_athlete_delete_view, name="staff_athlete_delete"),

    path("staff/assessments/create/", views.assessment_session_create_view, name="assessment_create"),
    path("staff/assessments/<int:session_id>/capture/", views.assessment_capture_view, name="assessment_capture"),
    path("staff/assessments/<int:session_id>/publish/", views.assessment_publish_view, name="assessment_publish"),
    path(
        "staff/assessments/protocol-metrics/",
        views.protocol_metric_definition_partial,
        name="protocol_metric_partial",
    ),
    path("contact/form/", views.contact_form_partial, name="contact_form_partial"),
    path("contact/submit/", views.submit_contact_form, name="contact_submit"),
    path("contact/close/", views.close_contact_modal, name="contact_close"),
    path("athlete/session/<int:session_id>/", views.athlete_session_detail_view, name="athlete_session_detail"),
    path(
    "staff/assessments/athlete-enrollments/",
    views.athlete_enrollment_partial,
    name="athlete_enrollment_partial",
    ),
    path(
    "staff/assessments/domain-framework-protocol/",
    views.domain_framework_protocol_partial,
    name="domain_framework_protocol_partial",
    ),
    path("staff/assessments/<int:session_id>/mark-complete/", views.assessment_mark_complete_view, name="assessment_mark_complete"),
]