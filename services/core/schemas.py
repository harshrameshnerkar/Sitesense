"""
Pydantic Schemas for Request and Response validation across SiteSense APIs.
Enforces typed contracts and standard error structures.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr


# ==========================================
# 1. Global Standard Error Shape
# ==========================================
class ErrorDetail(BaseModel):
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error description")
    detail: Optional[str] = Field(None, description="Technical detail or trace information")


class ErrorResponse(BaseModel):
    error: ErrorDetail


# ==========================================
# 2. Authentication Schemas
# ==========================================
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserSummary(BaseModel):
    id: int
    employee_id: Optional[str] = None
    name: str
    email: str
    role: str
    department: Optional[str] = None
    shift: Optional[str] = None
    phone: Optional[str] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    token: str
    user: UserSummary


# ==========================================
# 3. Site Schemas
# ==========================================
class SiteResponse(BaseModel):
    id: int
    name: str
    type: str
    location: str
    active: bool = True

    class Config:
        from_attributes = True


# ==========================================
# 4. Inspection & Ingestion Schemas
# ==========================================
class InspectionCreateResponse(BaseModel):
    inspection_id: int
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    status: str  # queued, processing, completed, failed
    progress: int = Field(..., ge=0, le=100)
    result_id: Optional[int] = None
    error: Optional[str] = None


class InspectionListItem(BaseModel):
    id: int
    site: str
    date: str
    status: str
    pass_rate: float


class DetectionItem(BaseModel):
    id: int
    class_name: str
    bbox: List[int] = Field(..., description="Strictly [x_min, y_min, x_max, y_max] in absolute pixel coordinates")
    confidence: float
    zone: Optional[str] = None
    frame_no: int = 0

    class Config:
        from_attributes = True


class ExtractionItem(BaseModel):
    id: int
    field_name: str
    value: str
    confidence: float
    review_status: str

    class Config:
        from_attributes = True


class FindingItem(BaseModel):
    id: int
    rule_name: str
    policy_ref: str
    status: str  # pass, fail, review
    explanation: str
    evidence_ids: List[int] = []


class MediaItem(BaseModel):
    id: int
    type: str
    filename: str
    path: str
    annotated_path: Optional[str] = None

    class Config:
        from_attributes = True


class InspectionDetailResponse(BaseModel):
    inspection_id: int
    site_name: str
    status: str
    created_at: str
    summary: Optional[str] = None
    media: List[MediaItem] = []
    detections: List[DetectionItem] = []
    extractions: List[ExtractionItem] = []
    findings: List[FindingItem] = []


# ==========================================
# 5. Review Queue Schemas
# ==========================================
class ReviewItem(BaseModel):
    id: int
    type: str  # extraction, detection
    media_id: int
    field_name: Optional[str] = None
    proposed_value: str
    confidence: float


class ReviewActionRequest(BaseModel):
    action: str = Field(..., description="accept, correct, reject")
    corrected_value: Optional[str] = None


class ReviewActionResponse(BaseModel):
    id: int
    status: str
    reviewed_by: int


# ==========================================
# 6. Conversational Agent & Trace Schemas
# ==========================================
class ChatRequest(BaseModel):
    question: str
    image_base64: Optional[str] = None
    session_id: Optional[str] = None


class ToolCallRecord(BaseModel):
    tool: str
    arguments: Dict[str, Any]
    output: Any


class AgentTraceResponse(BaseModel):
    route: str
    tools: List[ToolCallRecord]
    tokens: int
    cost: float
    latency: float


# ==========================================
# 7. Management Dashboard Schemas
# ==========================================
class DashboardMetricsResponse(BaseModel):
    inspections: int
    pass_rate: float
    top_failing_rules: List[Dict[str, Any]]
    pending_review: int


# ==========================================
# 8. Rules & Tickets Schemas
# ==========================================
class RuleResponse(BaseModel):
    id: int
    name: str
    type: str
    parameters: Dict[str, Any]
    policy_ref: str

    class Config:
        from_attributes = True


class RuleCreateRequest(BaseModel):
    name: str
    type: str
    parameters: Dict[str, Any] = {}
    policy_ref: str


class TicketCreateRequest(BaseModel):
    finding_id: int
    description: str
    approved: bool = True


class TicketResponse(BaseModel):
    ticket_id: int
    status: str


# ==========================================
# 9. Zone & Policy Schemas
# ==========================================
class ZoneConfigResponse(BaseModel):
    zones: List[Dict[str, Any]]
    lines: List[Dict[str, Any]]


class ZoneSaveRequest(BaseModel):
    site_id: int
    zones: List[Dict[str, Any]]
    lines: List[Dict[str, Any]]


class PolicyIngestResponse(BaseModel):
    policy_id: int
    chunks_created: int


# ==========================================
# 10. Audit Schemas
# ==========================================
class AuditLogItem(BaseModel):
    timestamp: str
    user: str
    action: str
    detail: str

