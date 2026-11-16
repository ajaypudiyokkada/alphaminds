"""
MTQ scoring engine.

MTQ48 captures 9 sub-scales across 4 pillars + 1 overall score (all on 1-10 scale):

  Commitment:  Goal Orientation, Achievement Orientation
  Control:     Control (Life), Control (Self)
  Challenge:   Risk Orientation, Learning Orientation
  Confidence:  Confidence (Abilities), Confidence (Interpersonal)

  Overall Mental Toughness: reported directly

Program recommendation thresholds (on the 1-10 overall score):
  ≤ 4   → 6-month intensive
  5 – 7 → 3-month program
  ≥ 8   → one-off sessions
"""
from __future__ import annotations

from decimal import Decimal

from assessments.models import AssessmentMetricValue, AssessmentSession
from programs.models import ProgramTypeChoices


# Metric names as they appear in MetricDefinition (seeded from Excel)
MTQ_METRIC_NAMES = [
    "Overall Mental Toughness",
    "Control (Life)",
    "Control (Self)",
    "Goal Orientation",
    "Achievement Orientation",
    "Risk Orientation",
    "Learning Orientation",
    "Confidence (Abilities)",
    "Confidence (Interpersonal)",
]

MTQ_THRESHOLDS = {
    # (min_score_inclusive, max_score_inclusive) → program_type
    (0, 4): ProgramTypeChoices.SIX_MONTH,
    (5, 7): ProgramTypeChoices.THREE_MONTH,
    (8, 10): ProgramTypeChoices.ONE_OFF,
}


def get_mtq_scores(session: AssessmentSession) -> dict[str, Decimal | None]:
    """Return a dict of {metric_name: numeric_value} for MTQ metrics in a session."""
    values = (
        AssessmentMetricValue.objects
        .filter(
            assessment_session=session,
            metric_definition__protocol__framework__name="MTQ Assessment",
            is_active=True,
        )
        .select_related("metric_definition")
    )
    return {v.metric_definition.name: v.numeric_value for v in values}


def compute_mtq_total(scores: dict[str, Decimal | None]) -> Decimal | None:
    """
    Return the overall MTQ score.

    If 'Overall Mental Toughness' was captured directly, use it.
    Otherwise, average all sub-scale scores.
    """
    overall = scores.get("Overall Mental Toughness")
    if overall is not None:
        return overall

    sub_scores = [v for k, v in scores.items() if v is not None and k != "Overall Mental Toughness"]
    if not sub_scores:
        return None
    return Decimal(str(round(sum(sub_scores) / len(sub_scores), 2)))


def recommend_program_type(total_score: Decimal) -> str:
    """Map an MTQ total score (1-10) to a ProgramTypeChoices value."""
    score_int = int(total_score)
    for (lo, hi), program_type in MTQ_THRESHOLDS.items():
        if lo <= score_int <= hi:
            return program_type
    # fallback
    return ProgramTypeChoices.THREE_MONTH
