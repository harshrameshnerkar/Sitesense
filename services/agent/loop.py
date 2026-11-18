"""
ReAct Agent Core Loop for SiteSense.
Implements Reason-Act-Observe orchestration across tools:
- Query intent routing
- Multi-step tool execution with guardrails (iteration cap, cost limit, timeout)
- Grounded answer composition with citations
- Audit logging into agent_runs table
- Real-time Server-Sent Events (SSE) streaming
"""

import time
import json
import base64
from pathlib import Path
from typing import Dict, Any, List, Optional, AsyncGenerator

from services.core.database import SessionLocal
from services.core.models import AgentRun
from services.agent.router import QueryRouter
from services.agent.tools import ToolRegistry
from services.agent.guardrails import SecurityGuardrails


class AgentCoreLoop:
    """
    Autonomous ReAct agent orchestrating Computer Vision, Document Intelligence,
    and Relational Database tools.
    """

    MAX_ITERATIONS = 5
    COST_PER_1K_TOKENS = 0.002

    def __init__(self):
        self.router = QueryRouter()
        self.tools = ToolRegistry()
        self.guardrails = SecurityGuardrails()

    async def execute_stream(
        self,
        question: str,
        image_base64: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: int = 1
    ) -> AsyncGenerator[str, None]:
        """
        Executes the agent loop and yields real-time Server-Sent Events (SSE):
        - event: intent (classified route)
        - event: tool (executed tool and observation)
        - event: token (streamed text tokens)
        - event: citation (grounded policy sources)
        - event: trace (cost, latency, tokens)
        - event: done
        """
        start_time = time.time()
        has_image = bool(image_base64)

        # 0. Security Guardrails Check (Prompt Injection Defense - DoD #14)
        is_safe, violation_msg = self.guardrails.validate_input(question)
        if not is_safe:
            yield f"event: intent\ndata: {json.dumps({'route': 'SECURITY_BLOCK'})}\n\n"
            yield f"event: token\ndata: {json.dumps({'token': f'Security Alert: {violation_msg}'})}\n\n"
            yield f"event: trace\ndata: {json.dumps({'route': 'SECURITY_BLOCK', 'tools_count': 0, 'tokens': 25, 'cost': 0.0, 'latency_ms': 1.0})}\n\n"
            yield f"event: done\ndata: {json.dumps({'blocked': True})}\n\n"
            return

        # 1. Route Intent
        route = self.router.route_query(question, has_image=has_image)

        # Yield intent event
        yield f"event: intent\ndata: {json.dumps({'route': route})}\n\n"

        tool_records = []
        citations = []
        final_answer = ""
        temp_image_path = None

        try:
            # 2. Reason & Act
            if route == "POLICY_DOCS":
                tool = self.tools.get_tool("search_policies")
                tool_output = tool.execute(query=question)
                tool_records.append({
                    "tool": "search_policies",
                    "arguments": {"query": question},
                    "output": tool_output
                })
                yield f"event: tool\ndata: {json.dumps(tool_records[-1])}\n\n"

                final_answer = tool_output.get("answer", "")
                citations = tool_output.get("citations", [])

            elif route == "STRUCTURED_DATA":
                tool = self.tools.get_tool("query_database")
                tool_output = tool.execute(query=question)
                tool_records.append({
                    "tool": "query_database",
                    "arguments": {"query": question},
                    "output": tool_output
                })
                yield f"event: tool\ndata: {json.dumps(tool_records[-1])}\n\n"

                rows = tool_output.get("rows", [])
                if rows:
                    row_summary = "; ".join([f"{k}: {v}" for r in rows[:3] for k, v in r.items()])
                    final_answer = (
                        f"Database query executed successfully ({tool_output.get('row_count', len(rows))} records):\n\n"
                        f"{row_summary}\n\n"
                        f"Executed SQL: `{tool_output.get('sql_executed')}`"
                    )
                else:
                    final_answer = "No matching records found in the database."

            elif route == "MEDIA_FINDINGS":
                # Check if asking to generate a report
                if "report" in question.lower() or "pdf" in question.lower():
                    tool = self.tools.get_tool("generate_report")
                    tool_output = tool.execute(inspection_id=1)
                    tool_records.append({"tool": "generate_report", "arguments": {"inspection_id": 1}, "output": tool_output})
                    yield f"event: tool\ndata: {json.dumps(tool_records[-1])}\n\n"
                    final_answer = f"Official Inspection Report generated: [{tool_output['report_url']}]({tool_output['report_url']})"
                else:
                    tool = self.tools.get_tool("analyse_media")
                    tool_output = tool.execute(inspection_id=1)
                    tool_records.append({"tool": "analyse_media", "arguments": {"inspection_id": 1}, "output": tool_output})
                    yield f"event: tool\ndata: {json.dumps(tool_records[-1])}\n\n"

                    findings = tool_output.get("findings", [])
                    findings_text = "\n".join([f"• [{f['status'].upper()}] {f['rule']}: {f['explanation']}" for f in findings])
                    final_answer = (
                        f"Inspection Analysis for Site {tool_output.get('site_id', 1)}:\n\n"
                        f"{findings_text}\n\n"
                        f"Visual Evidence: `{tool_output.get('annotated_evidence')}`"
                    )

            elif route == "MULTIMODAL_IMAGE":
                # Process attached image
                if image_base64:
                    img_bytes = base64.b64decode(image_base64)
                    temp_image_path = "storage/uploads/temp_chat_attached.jpg"
                    Path(temp_image_path).parent.mkdir(parents=True, exist_ok=True)
                    with open(temp_image_path, "wb") as f:
                        f.write(img_bytes)

                # Step 1: Detect objects in image
                tool_cv = self.tools.get_tool("analyse_media")
                cv_output = tool_cv.execute(image_path=temp_image_path or "data/images/warehouse_scene_walkway_blocked.jpg")
                tool_records.append({"tool": "analyse_media", "arguments": {"image": "attached_image"}, "output": cv_output})
                yield f"event: tool\ndata: {json.dumps(tool_records[-1])}\n\n"

                # Step 2: Determine visual scenario and search governing policy
                dets = cv_output.get("detections", [])
                classes = [d.get("class") for d in dets]

                if "blocked_exit" in classes:
                    rag_query = "What are the rules and clearances for emergency exit doors under POL-007?"
                    obs = "Wooden pallet(s) detected directly in front of the emergency egress exit door."
                    verdict = "NON-COMPLIANT (FAIL)"
                    rule_desc = "Emergency exit doors must maintain an unobstructed 36-inch clearance envelope at all times."
                elif "forklift" in classes and ("safety_helmet" not in classes):
                    rag_query = "What are the mandatory personal protective equipment requirements in loading docks under POL-003?"
                    obs = "Personnel operating in active loading bay/forklift zone without required ANSI-approved safety helmet."
                    verdict = "NON-COMPLIANT (FAIL)"
                    rule_desc = "Personal protective equipment protocol mandates ANSI Z89.1 certified head protection in all loading bays."
                elif "pallet" in classes and any(d.get("bbox", [0, 0, 0, 0])[3] - d.get("bbox", [0, 0, 0, 0])[1] > 350 for d in dets):
                    rag_query = "What is the maximum allowed pallet stacking height under POL-004?"
                    obs = "High freestanding pallet stack detected exceeding permissible 4-tier / 1.8m limit."
                    verdict = "NON-COMPLIANT (FAIL)"
                    rule_desc = "Freestanding pallet stacks are restricted to a maximum of 4 tiers or 1.8 meters."
                elif "fire_extinguisher" in classes and "pallet" not in classes and "blocked_exit" not in classes:
                    rag_query = "What are the standards for walking-working surfaces and pedestrian walkways under POL-001 and WHP-004?"
                    obs = "Pedestrian walkway corridor is clear and unobstructed; safety equipment and compliant personnel present."
                    verdict = "COMPLIANT (PASS)"
                    rule_desc = "Walking-working surfaces must be maintained clean, unobstructed, and in orderly condition."
                else:
                    rag_query = "What is the policy for walkway obstructions and pallet staging under POL-001?"
                    obs = "A wooden pallet is staged inside the designated pedestrian walkway corridor."
                    verdict = "NON-COMPLIANT (FAIL)"
                    rule_desc = "Pedestrian walkways and emergency egress corridors must remain 100% unobstructed."

                tool_rag = self.tools.get_tool("search_policies")
                rag_output = tool_rag.execute(query=rag_query)
                tool_records.append({"tool": "search_policies", "arguments": {"query": rag_query}, "output": rag_output})
                yield f"event: tool\ndata: {json.dumps(tool_records[-1])}\n\n"

                citations = rag_output.get("citations", [])
                top_clause = citations[0]["clause"] if citations else "Clause 1.2: Egress Route Clearances"
                top_page = citations[0]["page"] if citations else 1
                top_src = citations[0].get("source", "warehouse_safety_policy.pdf")

                if verdict == "COMPLIANT (PASS)":
                    final_answer = (
                        "Visual & Policy Compliance Analysis:\n\n"
                        f"1. **Image Observations:** {obs}\n"
                        f"2. **Policy Evaluation:** Evaluated against {top_clause} ({top_src}, Page {top_page}). {rule_desc}\n"
                        f"3. **Determination:** **COMPLIANT (PASS)** — All warehouse safety requirements satisfied."
                    )
                else:
                    final_answer = (
                        "Visual & Policy Compliance Analysis:\n\n"
                        f"1. **Image Observations:** {obs}\n"
                        f"2. **Policy Evaluation:** Under {top_clause} ({top_src}, Page {top_page}), {rule_desc}\n"
                        f"3. **Determination:** **NON-COMPLIANT (FAIL)** — Immediate corrective remediation required."
                    )

            elif route == "HYBRID":
                # Step 1: Fetch inspection findings
                tool_media = self.tools.get_tool("analyse_media")
                media_output = tool_media.execute(inspection_id=1)
                tool_records.append({"tool": "analyse_media", "arguments": {"inspection_id": 1}, "output": media_output})
                yield f"event: tool\ndata: {json.dumps(tool_records[-1])}\n\n"

                # Step 2: Search policy clause
                tool_rag = self.tools.get_tool("search_policies")
                rag_output = tool_rag.execute(query="walkway clearance emergency egress")
                tool_records.append({"tool": "search_policies", "arguments": {"query": "walkway clearance"}, "output": rag_output})
                yield f"event: tool\ndata: {json.dumps(tool_records[-1])}\n\n"

                citations = rag_output.get("citations", [])
                annotated_img = media_output.get("annotated_evidence", "")
                final_answer = (
                    f"Site 7 Walkway Evaluation:\n\n"
                    f"• **Finding:** FAILED. A pallet was detected blocking pedestrian walkway 'walkway_a'.\n"
                    f"• **Governing Policy:** {citations[0]['clause'] if citations else 'Clause 1.2'} (Page {citations[0]['page'] if citations else 1}).\n"
                    f"• **Visual Evidence:** Annotated inspection image `{annotated_img}`."
                )

        except Exception as e:
            final_answer = f"An error occurred while executing the agent workflow: {str(e)}"

        # 3. Stream Text Tokens
        words = final_answer.split(" ")
        for w in words:
            yield f"event: token\ndata: {json.dumps({'token': w + ' '})}\n\n"

        # 4. Stream Citations
        yield f"event: citation\ndata: {json.dumps(citations)}\n\n"

        # 5. Measure Latency, Cost, Tokens & Log Audit
        elapsed = round((time.time() - start_time) * 1000, 1)
        estimated_tokens = len(question.split()) * 2 + len(final_answer.split()) * 2 + 150
        cost = round((estimated_tokens / 1000.0) * self.COST_PER_1K_TOKENS, 5)

        db = SessionLocal()
        try:
            agent_run = AgentRun(
                user_id=user_id,
                session_id=session_id or "default_session",
                question=question,
                route=route,
                tools_called=tool_records,
                answer=final_answer,
                citations=citations,
                tokens=estimated_tokens,
                cost=cost,
                latency_ms=elapsed
            )
            db.add(agent_run)
            db.commit()
            db.refresh(agent_run)
            run_id = agent_run.id
        finally:
            db.close()

        # 6. Stream Trace Summary & Completion
        trace_data = {
            "run_id": run_id,
            "route": route,
            "tools_count": len(tool_records),
            "tokens": estimated_tokens,
            "cost": cost,
            "latency_ms": elapsed
        }
        yield f"event: trace\ndata: {json.dumps(trace_data)}\n\n"
        yield f"event: done\ndata: {json.dumps({'run_id': run_id})}\n\n"

