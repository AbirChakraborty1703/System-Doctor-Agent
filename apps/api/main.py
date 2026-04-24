"""FastAPI service for SystemDoctor AI orchestration endpoints."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from agents.orchestrator import OrchestratorAgent
from packages.schemas import DeviceMetadata, Question

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SystemDoctor AI API",
    version="1.0.0",
    description="Enterprise AI-powered system diagnostics and remediation API",
)

# CORS configuration uses ALLOWED_ORIGINS to keep production deploys configurable.
allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",")
    if origin.strip()
]
allow_credentials = "*" not in allowed_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = OrchestratorAgent()


# Add middleware for security headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "microphone=(), camera=(), geolocation=(), payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()"
    return response


class StartSessionRequest(BaseModel):
    issue: str = Field(..., min_length=1, max_length=4000)
    metadata: DeviceMetadata = DeviceMetadata()


class AnswerRequest(BaseModel):
    question_id: str = Field(..., min_length=1, max_length=128)
    question: str = Field(..., min_length=1, max_length=1000)
    target_signal: str = Field(..., min_length=1, max_length=128)
    answer: str = Field(..., min_length=1, max_length=4000)


class VerifyRequest(BaseModel):
    feedback: str = Field(..., min_length=1, max_length=1000)


@app.get("/health")
def health() -> dict:
    """Health check endpoint."""
    logger.info("Health check requested")
    return {"status": "ok", "service": "SystemDoctor AI API"}


@app.get("/api/v1/app/event/open")
def app_event_open() -> dict:
    """Compatibility endpoint for Streamlit component initialization."""
    logger.info("App event open requested")
    return {"status": "ok", "message": "SystemDoctor AI is ready"}


@app.post("/api/v1/app/event/open")
def app_event_open_post() -> dict:
    """Compatibility endpoint for Streamlit component initialization (POST)."""
    logger.info("App event open POST requested")
    return {"status": "ok", "message": "SystemDoctor AI is ready"}


@app.post("/sessions")
def start_session(payload: StartSessionRequest) -> dict:
    issue = payload.issue.strip()
    if not issue:
        raise HTTPException(status_code=422, detail="Issue must not be blank")

    session = orchestrator.start_session(issue, payload.metadata)
    question = orchestrator.next_question(session)
    return {
        "session_id": session.session_id,
        "status": session.status.value,
        "question": question.model_dump(mode="json") if question else None,
    }


@app.get("/sessions/{session_id}")
def get_session(session_id: str) -> dict:
    session = orchestrator.load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.to_storage_dict()


@app.post("/sessions/{session_id}/answer")
def submit_answer(session_id: str, payload: AnswerRequest) -> dict:
    session = orchestrator.load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    answer = payload.answer.strip()
    if not answer:
        raise HTTPException(status_code=422, detail="Answer must not be blank")

    question = Question(
        id=payload.question_id,
        text=payload.question,
        target_signal=payload.target_signal,
        information_gain=0.0,
    )
    orchestrator.submit_answer(session, question, answer)

    session = orchestrator.load_session(session_id)
    if not session:
        raise HTTPException(status_code=500, detail="Failed to reload session")

    next_question = orchestrator.next_question(session)
    if next_question is None:
        session = orchestrator.run_diagnosis(session)
        session = orchestrator.build_remediation(session)

    return {
        "status": session.status.value,
        "next_question": next_question.model_dump(mode="json") if next_question else None,
        "diagnoses": [item.model_dump(mode="json") for item in session.diagnoses],
    }


@app.post("/sessions/{session_id}/verify")
def verify(session_id: str, payload: VerifyRequest) -> dict:
    session = orchestrator.load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    feedback = payload.feedback.strip()
    if not feedback:
        raise HTTPException(status_code=422, detail="Feedback must not be blank")

    result = orchestrator.verify(session, feedback)
    session = orchestrator.load_session(session_id)
    if not session:
        raise HTTPException(status_code=500, detail="Failed to reload session")

    if result.next_action == "refine_and_retry":
        next_question: Optional[Question] = orchestrator.next_question(session)
        if next_question is None:
            session = orchestrator.run_diagnosis(session)
            session = orchestrator.build_remediation(session)
    else:
        next_question = None

    return {
        "verification": result.model_dump(mode="json"),
        "status": session.status.value,
        "next_question": next_question.model_dump(mode="json") if next_question else None,
    }


# Global exception handler for comprehensive error responses
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": "An unexpected server error occurred.",
            "status": 500,
        },
    )
