"""
Compliance Rules Management Route for SiteSense.
Lists and creates machine-readable rules linked to policy clauses.
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from services.core.database import get_db
from services.core.models import Rule
from services.core.schemas import RuleResponse, RuleCreateRequest

router = APIRouter(prefix="/rules", tags=["Rules"])


@router.get("", response_model=List[RuleResponse])
def list_rules(db: Session = Depends(get_db)):
    """
    List all active machine-readable compliance rules.
    """
    rules = db.query(Rule).filter(Rule.active == True).all()
    return [
        RuleResponse(
            id=r.id,
            name=r.name,
            type=r.rule_type,
            parameters=r.parameters or {},
            policy_ref=r.policy_ref
        )
        for r in rules
    ]


@router.post("", response_model=RuleResponse)
def create_rule(payload: RuleCreateRequest, db: Session = Depends(get_db)):
    """
    Register a new compliance rule referencing a written policy clause.
    """
    rule = Rule(
        name=payload.name,
        description=payload.name,
        rule_type=payload.type,
        parameters=payload.parameters,
        policy_ref=payload.policy_ref,
        active=True
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    return RuleResponse(
        id=rule.id,
        name=rule.name,
        type=rule.rule_type,
        parameters=rule.parameters or {},
        policy_ref=rule.policy_ref
    )

