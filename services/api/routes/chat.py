"""
Conversational Agent & Trace Route for SiteSense.
Provides streaming SSE chat responses via the ReAct AgentCoreLoop and audit trace inspection.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from services.core.database import get_db
from services.core.models import AgentRun
from services.core.schemas import ChatRequest, AgentTraceResponse, ToolCallRecord, ErrorResponse
from services.agent.loop import AgentCoreLoop

router = APIRouter(prefix="/chat", tags=["Agent Chat"])

# Global agent core instance
agent_loop = AgentCoreLoop()


@router.post("")
async def chat_with_agent(payload: ChatRequest):
    """
    Streaming chat endpoint for multi-intent operations Q&A.
    Streams token-by-token text, tool execution events, and grounded citations via SSE.
    """
    generator = agent_loop.execute_stream(
        question=payload.question,
        image_base64=payload.image_base64,
        session_id=payload.session_id,
        user_id=1
    )
    return StreamingResponse(generator, media_type="text/event-stream")


@router.get("/{run_id}/trace", response_model=AgentTraceResponse, responses={404: {"model": ErrorResponse}})
def get_agent_trace(run_id: int, db: Session = Depends(get_db)):
    """
    Retrieve full execution trace for an agent run (tools called, tokens, cost, latency).
    """
    run = db.query(AgentRun).filter(AgentRun.id == run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "TRACE_NOT_FOUND", "message": f"Agent run {run_id} not found", "detail": None}}
        )

    tools_record = [
        ToolCallRecord(tool=t.get("tool", ""), arguments=t.get("arguments", {}), output=t.get("output", ""))
        for t in (run.tools_called or [])
    ]

    return AgentTraceResponse(
        route=run.route,
        tools=tools_record,
        tokens=run.tokens,
        cost=run.cost,
        latency=run.latency_ms
    )
