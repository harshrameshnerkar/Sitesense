"""
Multi-Intent Query Router for SiteSense.
Classifies user queries into the appropriate analytical route:
- MEDIA_FINDINGS: Inspection observations, object detections, visual evidence
- POLICY_DOCS: Written compliance handbooks, clauses, rules
- STRUCTURED_DATA: Aggregate database analytics, counts, cross-site SQL
- MULTIMODAL_IMAGE: Queries with an attached image requiring visual policy judgment
- HYBRID: Multi-source questions requiring both media findings and policy retrieval
"""

import re
from typing import Dict, Any, Optional


class QueryRouter:
    """
    Classifies intent of natural language queries to route to optimal tools.
    """

    ROUTES = [
        "MEDIA_FINDINGS",
        "POLICY_DOCS",
        "STRUCTURED_DATA",
        "MULTIMODAL_IMAGE",
        "HYBRID"
    ]

    def route_query(self, query: str, has_image: bool = False) -> str:
        """
        Determine the execution route for a given query and context.
        """
        # 1. Attached image query takes precedence for multimodal route
        if has_image:
            return "MULTIMODAL_IMAGE"

        q_lower = query.lower()

        # 2. Check for Hybrid intent (asks for both site finding/evidence and policy clause)
        has_media_intent = any(k in q_lower for k in ["site", "detected", "evidence", "passed", "failed", "inspection", "annotated"])
        has_policy_intent = any(k in q_lower for k in ["policy", "clause", "handbook", "standard", "rule", "cite", "citation"])

        if ("cite" in q_lower or "clause" in q_lower) and ("site" in q_lower or "evidence" in q_lower):
            return "HYBRID"

        # 3. Check for Structured Data intent (aggregate SQL questions)
        data_keywords = [
            "how many", "which rule failed", "most often", "most frequently",
            "breakdown", "across all", "last month", "total sites", "count",
            "aggregate", "average", "statistics", "trend"
        ]
        if any(k in q_lower for k in data_keywords):
            return "STRUCTURED_DATA"

        # 4. Check for Media Findings intent
        media_keywords = [
            "detected", "what objects", "show me the evidence", "annotated visual",
            "inspection id", "generate an official pdf", "generate report", "camera", "clip"
        ]
        if any(k in q_lower for k in media_keywords):
            return "MEDIA_FINDINGS"

        # 5. Check for Policy Docs intent
        if has_policy_intent or any(k in q_lower for k in ["clearance", "helmet", "extinguisher", "pallet", "spill", "egress", "mandatory", "stacking"]):
            return "POLICY_DOCS"

        # Default fallback
        return "POLICY_DOCS"

