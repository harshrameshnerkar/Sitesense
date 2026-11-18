"""
Dashboard Analytics Route for SiteSense.
Calculates cross-site operational statistics and compliance metrics.
"""

from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from services.core.database import get_db
from services.core.models import Inspection, Finding, Extraction, Rule
from services.core.schemas import DashboardMetricsResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/metrics", response_model=DashboardMetricsResponse)
def get_dashboard_metrics(
    site_id: Optional[int] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Retrieve real-time aggregate operational KPIs across all sites.
    """
    insp_query = db.query(Inspection)
    if site_id:
        insp_query = insp_query.filter(Inspection.site_id == site_id)
    total_inspections = insp_query.count()

    # Calculate pass rate
    finding_query = db.query(Finding)
    total_findings = finding_query.count()
    passed_findings = finding_query.filter(Finding.status == "pass").count()
    pass_rate = round((passed_findings / total_findings * 100), 1) if total_findings > 0 else 100.0

    # Top failing rules
    top_rules = []
    fail_counts = (
        db.query(Finding.rule_id, func.count(Finding.id).label("count"))
        .filter(Finding.status == "fail")
        .group_by(Finding.rule_id)
        .order_by(func.count(Finding.id).desc())
        .limit(5)
        .all()
    )

    for rule_id, count in fail_counts:
        rule = db.query(Rule).filter(Rule.id == rule_id).first()
        top_rules.append({
            "rule_id": rule_id,
            "rule_name": rule.name if rule else f"Rule {rule_id}",
            "policy_ref": rule.policy_ref if rule else "",
            "failure_count": count
        })

    # Pending human review
    pending_review = db.query(Extraction).filter(Extraction.review_status == "pending_review").count()

    return DashboardMetricsResponse(
        inspections=total_inspections,
        pass_rate=pass_rate,
        top_failing_rules=top_rules,
        pending_review=pending_review
    )

