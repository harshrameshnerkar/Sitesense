"""
SQLAlchemy ORM Models for SiteSense.
Defines all 11 core tables specified in the architecture:
- sites, users, inspections, media, detections, extractions,
- policies, findings, rules, tickets, agent_runs.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, Float, Text,
    DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from services.core.database import Base


def utc_now() -> datetime:
    """Return current UTC timestamp with timezone awareness."""
    return datetime.now(timezone.utc)


class Site(Base):
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(100), default="warehouse")  # warehouse, retail, depot, construction
    location = Column(String(255), nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    inspections = relationship("Inspection", back_populates="site")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(50), nullable=True, unique=True, index=True)  # e.g., EMP-001
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="employee")  # admin, manager, supervisor, employee
    department = Column(String(100), nullable=True)  # e.g. EHS Safety, Logistics, Operations
    shift = Column(String(50), nullable=True)  # e.g. Morning Shift (06:00 - 14:30)
    phone = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    inspections = relationship("Inspection", back_populates="user")
    reviewed_extractions = relationship("Extraction", back_populates="reviewer")
    approved_tickets = relationship("Ticket", back_populates="approver")


class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_id = Column(String(100), unique=True, index=True, nullable=False)
    status = Column(String(50), default="queued", index=True)  # queued, processing, completed, failed
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    site = relationship("Site", back_populates="inspections")
    user = relationship("User", back_populates="inspections")
    media = relationship("Media", back_populates="inspection", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="inspection", cascade="all, delete-orphan")


class Media(Base):
    __tablename__ = "media"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False, index=True)
    type = Column(String(50), nullable=False)  # image, video, doc
    filename = Column(String(255), nullable=False)
    path = Column(String(500), nullable=False)
    annotated_path = Column(String(500), nullable=True)
    metadata_json = Column(JSON, default=dict)  # site_id, user_id, gps, timestamp, device
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    inspection = relationship("Inspection", back_populates="media")
    detections = relationship("Detection", back_populates="media", cascade="all, delete-orphan")
    extractions = relationship("Extraction", back_populates="media", cascade="all, delete-orphan")


class Detection(Base):
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, index=True)
    media_id = Column(Integer, ForeignKey("media.id"), nullable=False, index=True)
    class_name = Column(String(100), nullable=False, index=True)
    bbox = Column(JSON, nullable=False)  # strictly [x_min, y_min, x_max, y_max] in absolute pixel coordinates
    confidence = Column(Float, nullable=False)
    zone = Column(String(100), nullable=True)  # zone polygon name e.g. 'walkway_bay_3'
    frame_no = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    media = relationship("Media", back_populates="detections")


class Extraction(Base):
    __tablename__ = "extractions"

    id = Column(Integer, primary_key=True, index=True)
    media_id = Column(Integer, ForeignKey("media.id"), nullable=False, index=True)
    field_name = Column(String(100), nullable=False, index=True)
    value = Column(String(500), nullable=False)
    confidence = Column(Float, nullable=False)
    review_status = Column(String(50), default="auto_approved")  # auto_approved, pending_review, corrected, rejected
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    media = relationship("Media", back_populates="extractions")
    reviewer = relationship("User", back_populates="reviewed_extractions")


class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False)
    source_file = Column(String(500), nullable=False)
    effective_date = Column(String(50), nullable=False)
    chunks_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now)


class Rule(Base):
    __tablename__ = "rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    rule_type = Column(String(100), nullable=False)  # required_object_present, forbidden_object_absent, zone_clearance, dwell_time, document_match
    parameters = Column(JSON, default=dict)
    policy_ref = Column(String(255), nullable=False)  # citation link e.g. "Section 2.1, Page 3"
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    findings = relationship("Finding", back_populates="rule")


class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False, index=True)
    rule_id = Column(Integer, ForeignKey("rules.id"), nullable=False, index=True)
    status = Column(String(50), nullable=False)  # pass, fail, review
    evidence_ids = Column(JSON, default=list)  # list of detection IDs or media IDs
    explanation = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    inspection = relationship("Inspection", back_populates="findings")
    rule = relationship("Rule", back_populates="findings")
    ticket = relationship("Ticket", back_populates="finding", uselist=False)


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    finding_id = Column(Integer, ForeignKey("findings.id"), nullable=False, unique=True, index=True)
    status = Column(String(50), default="proposed")  # proposed, approved, in_progress, resolved, rejected
    description = Column(Text, nullable=False)
    created_by = Column(String(100), default="agent")  # 'agent' or username
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    approved_at = Column(DateTime, nullable=True)

    # Relationships
    finding = relationship("Finding", back_populates="ticket")
    approver = relationship("User", back_populates="approved_tickets")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_id = Column(String(100), nullable=True, index=True)
    question = Column(Text, nullable=False)
    route = Column(String(50), nullable=False)  # MEDIA_FINDINGS, POLICY_DOCS, STRUCTURED_DATA, MULTIMODAL_IMAGE, HYBRID
    tools_called = Column(JSON, default=list)  # list of {tool_name, arguments, result}
    answer = Column(Text, nullable=False)
    citations = Column(JSON, default=list)  # list of {source, page, detection_ids}
    tokens = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    latency_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=utc_now)

