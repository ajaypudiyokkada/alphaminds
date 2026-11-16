from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from django.db.models import Prefetch
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from functools import wraps
from django.utils import timezone

from athletes.models import AthleteEnrollment, Athlete
from assessments.models import AssessmentMetricValue, AssessmentSession
from profiles.models import AthletePersonalityProfile

from core.choices import AssessmentSessionStatusChoices, SourceTypeChoices
from kpis.models import KPIDomain, KPIFramework, KPIProtocol


from sports.models import Sport

from .forms import (
    AcademyLeadInquiryForm,
    AthleteLeadInquiryForm,
    AssessmentSessionCreateForm,
    DynamicMetricValueForm,
    StaffAthleteCreateForm
)
from .models import LeadInquiryType



from athletes.models import Athlete
from assessments.models import AssessmentMetricValue, AssessmentSession
from core.choices import AssessmentSessionStatusChoices, SourceTypeChoices
from .forms import AssessmentSessionCreateForm, DynamicMetricValueForm, StaffAthleteCreateForm

def staff_view_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        staff_profile = getattr(request.user, "staff_profile", None)
        if not request.user.is_authenticated or not staff_profile or not staff_profile.is_active:
            raise PermissionDenied("Staff access required.")
        return view_func(request, *args, **kwargs)
    return _wrapped

def _get_staff_center(user):
    staff_profile = getattr(user, "staff_profile", None)
    if not user.is_authenticated or not staff_profile or not staff_profile.is_active:
        raise PermissionDenied("Staff access required.")
    return staff_profile.center


def _staff_athlete_qs(user):
    center = _get_staff_center(user)
    return Athlete.objects.filter(
        enrollments__center=center,
        enrollments__is_active=True,
        is_active=True,
    ).distinct()


def _staff_session_qs(user):
    center = _get_staff_center(user)
    return AssessmentSession.objects.filter(
        center=center,
        is_active=True,
    )


def user_is_staff_role(user):
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name="Staff").exists())


def user_is_athlete_role(user):
    return user.is_authenticated and user.groups.filter(name="Athlete").exists()


def home_view(request):
    return render(request, "frontend/home.html")


def _safe_decimal(value):
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _metric_sort_key(value):
    return (
        value.metric_definition.protocol.framework.domain.display_order,
        value.metric_definition.protocol.framework.display_order,
        value.metric_definition.protocol.display_order,
        value.metric_definition.display_order,
        value.metric_definition.name,
    )
    
# @login_required
# def role_router_view(request):
#     if user_is_staff_role(request.user):
#         return redirect("frontend:staff_home")
#     if user_is_athlete_role(request.user):
#         return redirect("frontend:athlete_home")
#     messages.warning(request, "Your account does not have an assigned role yet.")
#     return redirect("frontend:home")

@login_required
def role_router_view(request):
    user = request.user

    if hasattr(user, "athlete_profile"):
        return redirect("frontend:athlete_home")

    if hasattr(user, "staff_profile") and user.staff_profile.is_active:
        return redirect("frontend:staff_home")

    return redirect("admin:index")

# @login_required
# @user_passes_test(user_is_athlete_role)
# def athlete_home_view(request):
#     return render(request, "frontend/athlete_home.html")

def _to_decimal(value):
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _normalize_metric_value(metric_value):
    """
    v0.1 pragmatic normalization:
    - decimal/integer:
        * if 0..10 => scale to percentage
        * if 0..100 => use as-is
        * otherwise clamp using metric min/max if available
        * fallback to 50
    - boolean:
        * True => 100, False => 0
    - text/date/json:
        * not used for score aggregation
    """
    metric = metric_value.metric_definition
    dtype = metric_value.value_data_type

    if dtype in ("integer", "decimal"):
        raw = _to_decimal(metric_value.numeric_value)
        if raw is None:
            return None

        if Decimal("0") <= raw <= Decimal("10"):
            return float(raw * Decimal("10"))

        if Decimal("0") <= raw <= Decimal("100"):
            return float(raw)

        min_v = _to_decimal(metric.min_value)
        max_v = _to_decimal(metric.max_value)

        if min_v is not None and max_v is not None and max_v > min_v:
            normalized = ((raw - min_v) / (max_v - min_v)) * Decimal("100")
            normalized = max(Decimal("0"), min(Decimal("100"), normalized))
            return float(normalized)

        return 50.0

    if dtype == "boolean":
        if metric_value.boolean_value is True:
            return 100.0
        if metric_value.boolean_value is False:
            return 0.0

    return None


def _score_band(score):
    if score >= 80:
        return "Strong"
    if score >= 60:
        return "Developing"
    return "Emerging"


def _score_color(score):
    if score >= 80:
        return "text-emerald-400 border-emerald-500/30 bg-emerald-500/10"
    if score >= 60:
        return "text-yellow-300 border-yellow-700/30 bg-yellow-500/10"
    return "text-red-300 border-red-500/30 bg-red-500/10"


def _display_metric_value(metric_value):
    if metric_value.display_value not in (None, ""):
        return metric_value.display_value
    if metric_value.numeric_value is not None:
        return metric_value.numeric_value
    if metric_value.text_value not in (None, ""):
        return metric_value.text_value
    if metric_value.boolean_value is not None:
        return "Yes" if metric_value.boolean_value else "No"
    if metric_value.date_value is not None:
        return metric_value.date_value
    if metric_value.json_value:
        return "Recorded"
    return "—"


def _display_metric_units(metric_value):
    if metric_value.units:
        return metric_value.units
    if getattr(metric_value, "metric_definition", None) and metric_value.metric_definition.units:
        return metric_value.metric_definition.units
    return ""


def _metric_value_sort_key(value):
    return (
        value.metric_definition.protocol.framework.domain.display_order,
        value.metric_definition.protocol.framework.name,
        value.metric_definition.protocol.framework.display_order,
        value.metric_definition.protocol.display_order,
        value.metric_definition.protocol.name,
        value.metric_definition.display_order,
        value.metric_definition.label or value.metric_definition.name,
        value.sequence_no,
        value.id,
    )


@login_required
@user_passes_test(user_is_athlete_role)
def athlete_home_view(request):
    athlete = getattr(request.user, "athlete_profile", None)
    if not athlete:
        messages.warning(request, "No athlete profile is linked to this login yet.")
        return render(
            request,
            "frontend/athlete_home.html",
            {
                "athlete": None,
                "domain_cards": [],
                "selected_domain": None,
                "domain_detail_metrics": [],
                "recent_sessions": [],
                "latest_personality": None,
                "latest_assessment_date": None,
                "primary_enrollment": None,
            },
        )

    primary_enrollment = (
        athlete.enrollments.filter(is_active=True, status="active")
        .select_related("center", "sport")
        .order_by("-start_date", "-id")
        .first()
    )

    recent_sessions = list(
        AssessmentSession.objects.filter(
            athlete=athlete,
            is_active=True,
        )
        .select_related("protocol", "protocol__framework", "protocol__framework__domain", "center", "sport")
        .order_by("-assessed_on")[:10]
    )

    latest_assessment_date = recent_sessions[0].assessed_on if recent_sessions else None

    latest_personality = (
        AthletePersonalityProfile.objects.filter(athlete=athlete, is_active=True)
        .select_related("personality_type")
        .order_by("-assessed_on", "-id")
        .first()
    )

    latest_metric_values = (
        AssessmentMetricValue.objects.filter(
            assessment_session__athlete=athlete,
            assessment_session__status=AssessmentSessionStatusChoices.PUBLISHED,
            assessment_session__is_active=True,
            is_active=True,
        )
        .select_related(
            "assessment_session",
            "metric_definition",
            "metric_definition__protocol",
            "metric_definition__protocol__framework",
            "metric_definition__protocol__framework__domain",
        )
        .order_by(
            "metric_definition_id",
            "-assessment_session__assessed_on",
            "-assessment_session_id",
            "-id",
        )
    )

    latest_by_metric = {}
    for value in latest_metric_values:
        if value.metric_definition_id not in latest_by_metric:
            latest_by_metric[value.metric_definition_id] = value

    domain_bucket = defaultdict(list)
    for value in latest_by_metric.values():
        domain = value.metric_definition.protocol.framework.domain
        domain_bucket[domain].append(value)

    domain_cards = []
    for domain, values in domain_bucket.items():
        normalized_scores = []
        metric_count = 0

        for value in values:
            metric_count += 1
            normalized = _normalize_metric_value(value)
            if normalized is not None:
                normalized_scores.append(normalized)

        score = round(sum(normalized_scores) / len(normalized_scores)) if normalized_scores else 0

        domain_cards.append(
            {
                "domain": domain,
                "score": score,
                "band": _score_band(score),
                "color_classes": _score_color(score),
                "metric_count": metric_count,
                "detail_url": f"{request.path}?domain={domain.id}",
            }
        )

    domain_cards.sort(key=lambda x: x["domain"].display_order)

    selected_domain = None
    domain_detail_metrics = []

    selected_domain_id = request.GET.get("domain")
    if selected_domain_id:
        for card in domain_cards:
            if str(card["domain"].id) == str(selected_domain_id):
                selected_domain = card["domain"]
                break

        if selected_domain:
            values = domain_bucket.get(selected_domain, [])
            values.sort(key=_metric_sort_key)

            for value in values:
                domain_detail_metrics.append(
                    {
                        "framework": value.metric_definition.protocol.framework.name,
                        "protocol": value.metric_definition.protocol.name,
                        "metric_name": value.metric_definition.label or value.metric_definition.name,
                        "display_value": _display_metric_value(value),
                        "units": _display_metric_units(value),
                        "assessed_on": value.assessment_session.assessed_on,
                    }
                )

    return render(
        request,
        "frontend/athlete_home.html",
        {
            "athlete": athlete,
            "domain_cards": domain_cards,
            "selected_domain": selected_domain,
            "domain_detail_metrics": domain_detail_metrics,
            "recent_sessions": recent_sessions,
            "latest_personality": latest_personality,
            "latest_assessment_date": latest_assessment_date,
            "primary_enrollment": primary_enrollment,
        },
    )

@login_required
@user_passes_test(user_is_staff_role)
def staff_home_view(request):
    center = _get_staff_center(request.user)

    athletes = _staff_athlete_qs(request.user).order_by("full_name")

    sessions = (
        _staff_session_qs(request.user)
        .select_related("athlete", "protocol")
        .order_by("-assessed_on", "-id")
    )

    now = timezone.now()

    context = {
        # ✅ REQUIRED by template
        "athlete_count": athletes.count(),
        "booked_sessions": sessions.filter(
            status=AssessmentSessionStatusChoices.BOOKED
        ).count(),

        # ⚠️ your template uses "Draft" → map it to COMPLETED
        "draft_sessions": sessions.filter(
            status=AssessmentSessionStatusChoices.COMPLETED
        ).count(),

        "published_sessions": sessions.filter(
            status=AssessmentSessionStatusChoices.PUBLISHED
        ).count(),

        "recent_sessions": sessions[:8],
        "athletes": athletes[:10],

        # ✅ keep your new workflow buckets (future use)
        "pending_assessments": sessions.filter(
            status=AssessmentSessionStatusChoices.BOOKED
        ).order_by("assessed_on"),

        "ready_to_complete": sessions.filter(
            status=AssessmentSessionStatusChoices.BOOKED,
            assessed_on__lte=now,
        ).order_by("assessed_on"),

        "ready_to_capture": sessions.filter(
            status=AssessmentSessionStatusChoices.COMPLETED,
        ).order_by("-assessed_on"),

        "ready_to_publish": sessions.filter(
            status=AssessmentSessionStatusChoices.COMPLETED,
            metric_values__is_active=True,
        ).exclude(
            status=AssessmentSessionStatusChoices.PUBLISHED,
        ).distinct().order_by("-assessed_on"),
    }

    return render(request, "frontend/staff_home.html", context)


@login_required
@user_passes_test(user_is_staff_role)
def protocol_metric_definition_partial(request):
    protocol_id = request.GET.get("protocol") or request.POST.get("protocol")
    metric_form = DynamicMetricValueForm(metric_definitions=[])

    if protocol_id:
        protocol = get_object_or_404(KPIProtocol, id=protocol_id, is_active=True)
        metric_definitions = protocol.metrics.filter(is_active=True).order_by("display_order", "id")
        metric_form = DynamicMetricValueForm(metric_definitions=metric_definitions)

        return render(
            request,
            "frontend/partials/protocol_metric_fields.html",
            {
                "selected_protocol": protocol,
                "metric_form": metric_form,
                "metric_definitions": metric_definitions,
            },
        )

    return render(
        request,
        "frontend/partials/protocol_metric_fields.html",
        {
            "selected_protocol": None,
            "metric_form": metric_form,
            "metric_definitions": [],
        },
    )


@login_required
@staff_view_required
def assessment_session_create_view(request):
    center = _get_staff_center(request.user)

    athlete_qs = _staff_athlete_qs(request.user).order_by("full_name")
    enrollment_qs = (
        AthleteEnrollment.objects.filter(
            center=center,
            is_active=True,
            athlete__is_active=True,
        )
        .select_related("athlete", "center", "sport")
        .order_by("-start_date", "-id")
    )

    domain_qs = KPIDomain.objects.filter(is_active=True).order_by("display_order", "name")
    framework_qs = KPIFramework.objects.filter(is_active=True).select_related("domain").order_by("display_order", "name")
    protocol_qs = KPIProtocol.objects.filter(is_active=True).select_related("framework", "framework__domain").order_by("display_order", "name")

    initial = {}
    selected_enrollment = None
    selected_domain = None
    selected_framework = None
    selected_protocol_id = None

    athlete_id = request.GET.get("athlete")
    if athlete_id:
        athlete = get_object_or_404(athlete_qs, pk=athlete_id)
        initial["athlete"] = athlete.pk
        selected_enrollment = enrollment_qs.filter(athlete=athlete).first()
        if selected_enrollment:
            initial["enrollment"] = selected_enrollment.pk
            initial["center"] = selected_enrollment.center_id
            initial["sport"] = selected_enrollment.sport_id

    form = AssessmentSessionCreateForm(
        request.POST or None,
        initial=initial,
        center=center,
        athlete_queryset=athlete_qs,
        enrollment_queryset=enrollment_qs,
        domain_queryset=domain_qs,
        framework_queryset=framework_qs,
        protocol_queryset=protocol_qs,
    )

    if request.method == "POST" and form.is_valid():
        session = form.save(commit=False)
        session.athlete = form.cleaned_data["athlete"]
        session.enrollment = form.cleaned_data["enrollment"]
        session.center = form.cleaned_data["center"]
        session.sport = form.cleaned_data["sport"]
        session.status = AssessmentSessionStatusChoices.BOOKED
        session.source = SourceTypeChoices.MANUAL
        session.full_clean()
        session.save()
        return redirect("frontend:staff_home")

    return render(request, "frontend/assessment_book.html", {
        "form": form,
        "center": center,
        "selected_enrollment": selected_enrollment,
        "selected_domain": selected_domain,
        "selected_framework": selected_framework,
        "selected_protocol_id": selected_protocol_id,
    })


def contact_form_partial(request):
    inquiry_type = request.GET.get("inquiry_type") or request.POST.get("inquiry_type")

    athlete_types = {
        LeadInquiryType.ATHLETE_MENTAL_TOUGHNESS,
        LeadInquiryType.ATHLETE_COGNITIVE_VISION,
        LeadInquiryType.ATHLETE_EMOTIONAL_REGULATION,
    }

    if inquiry_type in athlete_types:
        form = AthleteLeadInquiryForm(inquiry_type=inquiry_type)
        form_title = dict(LeadInquiryType.choices).get(inquiry_type, "Athlete Inquiry")
    elif inquiry_type == LeadInquiryType.ACADEMY_PARTNERSHIP:
        form = AcademyLeadInquiryForm(inquiry_type=inquiry_type)
        form_title = dict(LeadInquiryType.choices).get(inquiry_type, "Academy Inquiry")
    else:
        raise Http404("Invalid inquiry type.")

    return render(
        request,
        "frontend/partials/contact_modal.html",
        {
            "form": form,
            "inquiry_type": inquiry_type,
            "form_title": form_title,
        },
    )


def submit_contact_form(request):
    if request.method != "POST":
        raise Http404("Invalid request method.")

    inquiry_type = request.POST.get("inquiry_type")

    athlete_types = {
        LeadInquiryType.ATHLETE_MENTAL_TOUGHNESS,
        LeadInquiryType.ATHLETE_COGNITIVE_VISION,
        LeadInquiryType.ATHLETE_EMOTIONAL_REGULATION,
    }

    if inquiry_type in athlete_types:
        form = AthleteLeadInquiryForm(request.POST, inquiry_type=inquiry_type)
    elif inquiry_type == LeadInquiryType.ACADEMY_PARTNERSHIP:
        form = AcademyLeadInquiryForm(request.POST, inquiry_type=inquiry_type)
    else:
        raise Http404("Invalid inquiry type.")

    if form.is_valid():
        lead = form.save(commit=False)
        lead.metadata = {
            "source": "website_homepage",
            "submitted_from": "program_ctas",
        }
        lead.save()

        return render(
            request,
            "frontend/partials/contact_form_success.html",
            {
                "success_message": "Thank you. Your enquiry has been received. Our team will connect with you shortly.",
            },
        )

    return render(
        request,
        "frontend/partials/contact_form_fields.html",
        {
            "form": form,
            "inquiry_type": inquiry_type,
            "form_title": dict(LeadInquiryType.choices).get(inquiry_type, "Inquiry"),
        },
        status=400,
    )


def close_contact_modal(request):
    return HttpResponse("")

@login_required
@user_passes_test(user_is_athlete_role)
def athlete_session_detail_view(request, session_id):
    athlete = getattr(request.user, "athlete_profile", None)
    if not athlete:
        messages.warning(request, "No athlete profile is linked to this login yet.")
        return redirect("frontend:athlete_home")

    session = get_object_or_404(
        AssessmentSession.objects.select_related(
            "athlete",
            "center",
            "sport",
            "protocol",
            "protocol__framework",
            "protocol__framework__domain",
        ),
        id=session_id,
        athlete=athlete,
        is_active=True,
    )

    metrics_visible = session.status == AssessmentSessionStatusChoices.PUBLISHED

    grouped_payload = []
    if metrics_visible:
        session_values = list(
            AssessmentMetricValue.objects.filter(
                assessment_session=session,
                is_active=True,
            )
            .select_related(
                "metric_definition",
                "metric_definition__protocol",
                "metric_definition__protocol__framework",
                "metric_definition__protocol__framework__domain",
            )
            .order_by(
                "metric_definition__protocol__framework__domain__display_order",
                "metric_definition__protocol__framework__name",
                "metric_definition__protocol__framework__display_order",
                "metric_definition__protocol__display_order",
                "metric_definition__display_order",
                "sequence_no",
                "id",
            )
        )

        grouped_values = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        metric_ids = []

        for value in session_values:
            domain = value.metric_definition.protocol.framework.domain
            framework = value.metric_definition.protocol.framework
            protocol = value.metric_definition.protocol
            grouped_values[domain][framework][protocol].append(value)
            metric_ids.append(value.metric_definition_id)

        trend_rows = {}

        if metric_ids:
            trend_values = (
                AssessmentMetricValue.objects.filter(
                    assessment_session__athlete=athlete,
                    assessment_session__status=AssessmentSessionStatusChoices.PUBLISHED,
                    metric_definition_id__in=metric_ids,
                    assessment_session__is_active=True,
                    is_active=True,
                )
                .select_related(
                    "assessment_session",
                    "metric_definition",
                )
                .order_by("metric_definition_id", "-assessment_session__assessed_on", "-id")
            )

            grouped_trends = defaultdict(list)
            for value in trend_values:
                if len(grouped_trends[value.metric_definition_id]) < 10:
                    grouped_trends[value.metric_definition_id].append(value)

            for metric_id, values in grouped_trends.items():
                trend_rows[metric_id] = [
                    {
                        "assessed_on": value.assessment_session.assessed_on,
                        "display_value": _display_metric_value(value),
                        "units": _display_metric_units(value),
                    }
                    for value in reversed(values)
                ]

        for domain, framework_map in grouped_values.items():
            framework_items = []
            for framework, protocol_map in framework_map.items():
                protocol_items = []
                for protocol, values in protocol_map.items():
                    metric_items = []
                    values.sort(key=_metric_value_sort_key)

                    for value in values:
                        metric_items.append(
                            {
                                "value": value,
                                "metric_name": value.metric_definition.label or value.metric_definition.name,
                                "display_value": _display_metric_value(value),
                                "units": _display_metric_units(value),
                                "trend_values": trend_rows.get(value.metric_definition_id, []),
                            }
                        )
                    protocol_items.append(
                        {
                            "protocol": protocol,
                            "metrics": metric_items,
                        }
                    )

                protocol_items.sort(key=lambda x: (x["protocol"].display_order, x["protocol"].name))
                framework_items.append(
                    {
                        "framework": framework,
                        "protocols": protocol_items,
                    }
                )

            framework_items.sort(key=lambda x: (x["framework"].display_order, x["framework"].name))
            grouped_payload.append(
                {
                    "domain": domain,
                    "frameworks": framework_items,
                }
            )

        grouped_payload.sort(key=lambda x: (x["domain"].display_order, x["domain"].name))

    recent_sessions = list(
        AssessmentSession.objects.filter(athlete=athlete, is_active=True)
        .select_related("protocol", "protocol__framework", "protocol__framework__domain")
        .order_by("-assessed_on")[:5]
    )

    return render(
        request,
        "frontend/athlete_session_detail.html",
        {
            "athlete": athlete,
            "session": session,
            "grouped_payload": grouped_payload,
            "recent_sessions": recent_sessions,
            "metrics_visible": metrics_visible,
        },
    )
    
@login_required
@staff_view_required
def staff_athlete_create_view(request):
    staff_profile = getattr(request.user, "staff_profile", None)
    center = getattr(staff_profile, "center", None)

    form = StaffAthleteCreateForm(
        request.POST or None,
        center=center,
        sport_queryset=Sport.objects.all(),
    )

    if request.method == "POST" and form.is_valid():
        athlete = form.save()
        generated_password = getattr(athlete, "generated_password", None)
        if generated_password:
            messages.success(
                request,
                f"Login created for {athlete.full_name}. Username: {athlete.user.username} / "
                f"temporary password: {generated_password} (shown once, not stored; share it securely).",
            )
        return redirect("frontend:staff_home")

    return render(request, "frontend/staff_athlete_form.html", {"form": form})

@login_required
@staff_view_required
def staff_athlete_detail_view(request, athlete_id):
    athlete = get_object_or_404(_staff_athlete_qs(request.user), pk=athlete_id)

    sessions = (
        AssessmentSession.objects.filter(athlete=athlete, is_active=True)
        .select_related("protocol", "protocol__framework", "protocol__framework__domain")
        .order_by("-assessed_on")
    )

    return render(request, "frontend/staff_athlete_detail.html", {
        "athlete": athlete,
        "sessions": sessions,
    })

@login_required
@staff_view_required
def staff_athlete_update_view(request, athlete_id):
    athlete = get_object_or_404(_staff_athlete_qs(request.user), pk=athlete_id)

    form = StaffAthleteCreateForm(
        request.POST or None,
        instance=athlete,
        center=_get_staff_center(request.user),
        sport_queryset=None,
    )

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("frontend:staff_athlete_detail", athlete_id=athlete.id)

    return render(request, "frontend/staff_athlete_form.html", {
        "form": form,
        "athlete": athlete,
    })
    
@login_required
@staff_view_required
def staff_athlete_delete_view(request, athlete_id):
    athlete = get_object_or_404(_staff_athlete_qs(request.user), pk=athlete_id)

    if request.method == "POST":
        athlete.is_active = False
        athlete.save(update_fields=["is_active", "updated_at"])
        return redirect("frontend:staff_home")

    return render(request, "frontend/staff_athlete_confirm_delete.html", {
        "athlete": athlete,
    })
    
        
@login_required
@staff_view_required
def assessment_capture_view(request, session_id):
    session = get_object_or_404(_staff_session_qs(request.user), pk=session_id)

    if session.status not in {
        AssessmentSessionStatusChoices.COMPLETED,
        AssessmentSessionStatusChoices.PUBLISHED,
    }:
        messages.error(request, "Capture is available only after the assessment is completed.")
        return redirect("frontend:staff_athlete_detail", athlete_id=session.athlete_id)

    metrics = session.protocol.metrics.filter(is_active=True).order_by("display_order", "id")
    form = DynamicMetricValueForm(request.POST or None, metric_definitions=metrics)

    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            AssessmentMetricValue.objects.filter(
                assessment_session=session,
                is_active=True,
            ).delete()

            metric_instances = form.build_metric_value_instances(session)
            for instance in metric_instances:
                instance.full_clean()
            if metric_instances:
                AssessmentMetricValue.objects.bulk_create(metric_instances)

        messages.success(request, "Assessment metrics captured successfully.")
        return redirect("frontend:staff_athlete_detail", athlete_id=session.athlete_id)

    return render(request, "frontend/assessment_capture.html", {
        "session": session,
        "form": form,
    })
    
@login_required
@staff_view_required
def assessment_publish_view(request, session_id):
    session = get_object_or_404(_staff_session_qs(request.user), pk=session_id)

    has_metrics = session.metric_values.filter(is_active=True).exists()
    if session.status != AssessmentSessionStatusChoices.COMPLETED or not has_metrics:
        messages.error(request, "Only completed assessments with captured metrics can be published.")
        return redirect("frontend:staff_athlete_detail", athlete_id=session.athlete_id)

    if request.method == "POST":
        session.status = AssessmentSessionStatusChoices.PUBLISHED
        session.save(update_fields=["status", "updated_at"])
        messages.success(request, "Assessment metrics published successfully.")
        return redirect("frontend:staff_athlete_detail", athlete_id=session.athlete_id)

    return render(request, "frontend/assessment_publish.html", {"session": session})
    
@login_required
@staff_view_required
def athlete_enrollment_partial(request):
    center = _get_staff_center(request.user)
    athlete_id = request.GET.get("athlete")

    enrollments = AthleteEnrollment.objects.filter(
        center=center,
        is_active=True,
        athlete__is_active=True,
    ).select_related("athlete", "center", "sport").order_by("-start_date", "-id")

    if athlete_id:
        enrollments = enrollments.filter(athlete_id=athlete_id)
    else:
        enrollments = enrollments.none()

    selected = enrollments.first()

    return render(
        request,
        "frontend/partials/assessment_enrollment_fields.html",
        {
            "enrollments": enrollments,
            "selected_enrollment": selected,
        },
    )


@login_required
@staff_view_required
def domain_framework_protocol_partial(request):
    domain_id = request.GET.get("domain")
    framework_id = request.GET.get("framework")

    domains = KPIDomain.objects.filter(is_active=True).order_by("display_order", "name")
    frameworks = KPIFramework.objects.filter(is_active=True).select_related("domain").order_by("display_order", "name")
    protocols = KPIProtocol.objects.filter(is_active=True).select_related("framework", "framework__domain").order_by("display_order", "name")

    if domain_id:
        frameworks = frameworks.filter(domain_id=domain_id)
    else:
        frameworks = frameworks.none()

    if framework_id:
        protocols = protocols.filter(framework_id=framework_id)
    else:
        protocols = protocols.none()

    selected_domain = domains.filter(pk=domain_id).first() if domain_id else None
    selected_framework = frameworks.filter(pk=framework_id).first() if framework_id else None

    return render(
        request,
        "frontend/partials/assessment_protocol_fields.html",
        {
            "domains": domains,
            "frameworks": frameworks,
            "protocols": protocols,
            "selected_domain": selected_domain,
            "selected_framework": selected_framework,
        },
    )
    
@login_required
@staff_view_required
def assessment_mark_complete_view(request, session_id):
    session = get_object_or_404(_staff_session_qs(request.user), pk=session_id)

    if timezone.now() < session.assessed_on:
        messages.error(request, "Assessment can only be completed on or after the scheduled time.")
        return redirect("frontend:staff_home")

    if request.method == "POST":
        notes = request.POST.get("notes", "").strip()
        session.status = AssessmentSessionStatusChoices.COMPLETED
        if notes:
            session.notes = notes
        session.save(update_fields=["status", "notes", "updated_at"])
        return redirect("frontend:staff_athlete_detail", athlete_id=session.athlete_id)

    return render(request, "frontend/assessment_mark_complete.html", {"session": session})