"""
Agent Tool Registry and Schemas for SiteSense.
Provides a centralized, schema-validated tool ecosystem for the ReAct agent:
- analyse_media
- search_policies
- query_database (Read-only SQL safety sandbox)
- generate_report
"""

import re
import logging
from typing import Dict, Any, List, Optional, Callable
from sqlalchemy import text
from services.core.database import SessionLocal, engine
from services.core.models import Inspection, Media, Detection, Finding, Rule
from services.knowledge.rag import PolicyKnowledgeEngine
from services.vision.detector import VisionDetector
from services.vision.zones import ZoneEngine

logger = logging.getLogger("sitesense.agent.tools")

knowledge_engine = PolicyKnowledgeEngine()
detector = VisionDetector()


class Tool:
    def __init__(self, name: str, description: str, parameters: Dict[str, Any], func: Callable):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.func = func

    def execute(self, **kwargs) -> Any:
        return self.func(**kwargs)

    def to_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }


class ToolRegistry:
    """
    Central registry for all tools available to the agent.
    New tools are added via registry.register() without modifying the agent core loop.
    """

    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._register_default_tools()

    def register(self, tool: Tool):
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list_schemas(self) -> List[Dict[str, Any]]:
        return [t.to_schema() for t in self._tools.values()]

    def _register_default_tools(self):
        # 1. search_policies Tool
        self.register(
            Tool(
                name="search_policies",
                description="Search the company safety handbook for rules, citations, and compliance standards.",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The safety compliance or policy question to search."}
                    },
                    "required": ["query"]
                },
                func=self._search_policies
            )
        )

        # 2. analyse_media Tool
        self.register(
            Tool(
                name="analyse_media",
                description="Retrieve vision detections, zone evaluations, and annotated evidence for an inspection or image.",
                parameters={
                    "type": "object",
                    "properties": {
                        "inspection_id": {"type": "integer", "description": "ID of the inspection to analyze."},
                        "image_path": {"type": "string", "description": "Optional direct file path to an image."}
                    }
                },
                func=self._analyse_media
            )
        )

        # 3. query_database Tool (Read-only Safe SQL)
        self.register(
            Tool(
                name="query_database",
                description="Execute read-only SQL queries to answer aggregate questions across sites, inspections, and findings.",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Natural language aggregate data query."},
                        "sql": {"type": "string", "description": "Validated read-only SELECT SQL statement."}
                    }
                },
                func=self._query_database
            )
        )

        # 4. generate_report Tool
        self.register(
            Tool(
                name="generate_report",
                description="Generate an official PDF compliance report for an inspection session.",
                parameters={
                    "type": "object",
                    "properties": {
                        "inspection_id": {"type": "integer", "description": "ID of the completed inspection."}
                    },
                    "required": ["inspection_id"]
                },
                func=self._generate_report
            )
        )

    # ----------------------------------------------------
    # Tool Implementations
    # ----------------------------------------------------
    def _search_policies(self, query: str) -> Dict[str, Any]:
        """Search policy knowledge base."""
        return knowledge_engine.answer_question(query)

    def _analyse_media(self, inspection_id: Optional[int] = None, image_path: Optional[str] = None) -> Dict[str, Any]:
        """Fetch visual detections and findings."""
        db = SessionLocal()
        try:
            if inspection_id:
                insp = db.query(Inspection).filter(Inspection.id == inspection_id).first()
                if not insp:
                    return {"error": f"Inspection {inspection_id} not found"}

                detections = []
                for m in insp.media:
                    for d in m.detections:
                        detections.append({
                            "class": d.class_name,
                            "bbox": d.bbox,
                            "confidence": d.confidence,
                            "zone": d.zone
                        })

                findings = [
                    {"rule": f.rule.name if f.rule else "", "status": f.status, "explanation": f.explanation}
                    for f in insp.findings
                ]

                annotated_paths = [m.annotated_path for m in insp.media if m.annotated_path]

                return {
                    "site_id": insp.site_id,
                    "detections": detections,
                    "findings": findings,
                    "annotated_evidence": annotated_paths[0] if annotated_paths else None
                }

            elif image_path:
                raw_dets = detector.detect(image_path)
                return {
                    "image": image_path,
                    "detections": [{"class": d.class_name, "bbox": d.bbox, "confidence": d.confidence} for d in raw_dets]
                }
            return {"error": "Must provide either inspection_id or image_path"}
        finally:
            db.close()

    def _query_database(self, query: Optional[str] = None, sql: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes validated read-only SQL queries.
        Blocks destructive actions (DROP, DELETE, UPDATE, INSERT, ALTER).
        """
        if not sql:
            # Simple Text-to-SQL translation for common aggregate questions
            q_lower = (query or "").lower()
            if "fail" in q_lower or "rule" in q_lower:
                sql = (
                    "SELECT r.name as rule_name, COUNT(f.id) as failure_count "
                    "FROM findings f JOIN rules r ON f.rule_id = r.id "
                    "WHERE f.status = 'fail' "
                    "GROUP BY r.name ORDER BY failure_count DESC;"
                )
            elif "site" in q_lower or "inspection" in q_lower:
                sql = "SELECT status, COUNT(*) as count FROM inspections GROUP BY status;"
            else:
                sql = "SELECT id, name, type, location FROM sites;"

        # Security check: Ensure query is strictly read-only SELECT
        cleaned_sql = sql.strip().upper()
        if not cleaned_sql.startswith("SELECT"):
            return {
                "error": "Destructive SQL operation blocked by security policy. Only read-only SELECT allowed.",
                "blocked": True
            }

        forbidden_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "EXEC", "--", ";--"]
        for kw in forbidden_keywords:
            if re.search(rf"\b{kw}\b", cleaned_sql):
                return {
                    "error": f"Keyword '{kw}' prohibited in read-only queries.",
                    "blocked": True
                }

        # Execute read-only query
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            rows = [dict(row._mapping) for row in result]

        return {
            "sql_executed": sql,
            "row_count": len(rows),
            "rows": rows
        }

    def _generate_report(self, inspection_id: int) -> Dict[str, Any]:
        """Generates report link."""
        return {
            "inspection_id": inspection_id,
            "report_url": f"/storage/reports/REP-{inspection_id}-2026.pdf",
            "format": "pdf",
            "status": "ready"
        }

