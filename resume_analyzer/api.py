
"""FastAPI endpoints with anonymous session security."""

import threading

from contextlib import asynccontextmanager
from uuid import UUID
from .rate_limiter import AnalysisRateLimiter

from fastapi import (
    FastAPI,
    HTTPException,
    Header,
)
from fastapi.encoders import jsonable_encoder
from langgraph.types import Command
from pydantic import BaseModel, Field

from .graph import review_graph, checkpointer
from .schemas import (
    RequirementReview,
    ResumeEditDecision,
)
from .sessions import SessionStore

from groq import (
    RateLimitError,
    APITimeoutError,
    APIConnectionError,
)


session_store = SessionStore(checkpointer)
analysis_limiter = AnalysisRateLimiter(
    max_requests=30,
    window_seconds=3600,
    max_concurrent=2,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    stop_event = threading.Event()

    def cleanup_worker():
        while not stop_event.wait(30):
            session_store.cleanup_expired()

    worker = threading.Thread(
        target=cleanup_worker,
        daemon=True,
    )

    worker.start()

    try:
        yield

    finally:
        stop_event.set()
        worker.join(timeout=5)


app = FastAPI(
    title="Resume Analyzer API",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    debug=False,
    lifespan=lifespan,
)


class AnalysisRequest(BaseModel):
    resume: str = Field(
        min_length=1,
        max_length=100_000,
    )

    job_description: str = Field(
        min_length=1,
        max_length=40_000,
    )


class ReviewRequest(BaseModel):
    reviews: list[RequirementReview] = Field(
        default_factory=list,
        max_length=100,
    )

    additional_information: list[str] = Field(
        default_factory=list,
        max_length=20,
    )

    approved_for_optimization: bool = False


class EditReviewRequest(BaseModel):
    decisions: list[ResumeEditDecision] = Field(
        max_length=100,
    )


def graph_config(thread_id: str):
    return {
        "configurable": {
            "thread_id": thread_id
        }
    }


def build_response(thread_id: str, result: dict):
    snapshot = review_graph.get_state(
        graph_config(thread_id)
    )

    state = snapshot.values

    interrupts = [
        item.value
        for item in result.get("__interrupt__", ())
    ]

    return jsonable_encoder({
        "thread_id": thread_id,
        "status": (
            "paused" if interrupts else "completed"
        ),
        "next_nodes": list(snapshot.next),
        "interrupts": interrupts,
        "review_completed": state.get(
            "review_completed", False
        ),
        "match_score": state.get("match_score"),
        "hard_gaps": state.get("hard_gaps", []),
        "requirement_matches": state.get(
            "requirement_matches", []
        ),
        "resume_suggestions": state.get(
            "resume_suggestions"
        ),
        "edit_proposals": state.get(
            "edit_proposals", []
        ),
        "tailored_resume": state.get(
            "tailored_resume"
        ),
    })


def require_session_token(
    x_analysis_token: str | None = Header(
        default=None,
        max_length=256,
    ),
):
    if not x_analysis_token:
        raise HTTPException(
            status_code=401,
            detail="Analysis session token required",
        )

    return x_analysis_token


@app.get("/health")
def health():
    return {"status": "ok"}



@app.post("/analyses")
def start_analysis(request: AnalysisRequest):

    with analysis_limiter.admit():

        session_store.cleanup_expired()

        thread_id, token = session_store.create_session()

        try:
            with session_store.authorize(thread_id, token):
                result = review_graph.invoke(
                    request.model_dump(),
                    config=graph_config(thread_id),
                )

                response = build_response(thread_id, result)

            response["session_token"] = token
            return response

        except RateLimitError as exc:
            session_store.delete_session(thread_id)

            retry_after = exc.response.headers.get(
                "retry-after", "15"
            )

            if not retry_after.isdigit():
                retry_after = "15"

            raise HTTPException(
                status_code=503,
                detail=(
                    "Our AI service has reached its "
                    "temporary usage limit. "
                    "Please retry shortly."
                ),
                headers={
                    "Retry-After": retry_after
                },
            ) from None

        except (APITimeoutError, APIConnectionError):
            session_store.delete_session(thread_id)

            raise HTTPException(
                status_code=503,
                detail=(
                    "The AI service is temporarily "
                    "unavailable. Please try again."
                ),
            ) from None

        except Exception:
            session_store.delete_session(thread_id)
            raise


@app.post("/analyses/{thread_id}/review")
def submit_review(
    thread_id: UUID,
    request: ReviewRequest,
    x_analysis_token: str = Header(
        ...,
        max_length=256,
    ),
):
    thread = str(thread_id)

    with session_store.authorize(
        thread,
        x_analysis_token,
    ):
        config = graph_config(thread)

        snapshot = review_graph.get_state(config)

        if "human_review" not in snapshot.next:
            raise HTTPException(
                status_code=409,
                detail="Analysis is not awaiting review",
            )

        result = review_graph.invoke(
            Command(resume=request.model_dump()),
            config=config,
        )

        return build_response(thread, result)


@app.post("/analyses/{thread_id}/edits")
def submit_edit_decisions(
    thread_id: UUID,
    request: EditReviewRequest,
    x_analysis_token: str = Header(
        ...,
        max_length=256,
    ),
):
    thread = str(thread_id)

    with session_store.authorize(
        thread,
        x_analysis_token,
    ):
        config = graph_config(thread)

        snapshot = review_graph.get_state(config)

        if "review_resume_edits" not in snapshot.next:
            raise HTTPException(
                status_code=409,
                detail="Analysis is not awaiting edit decisions",
            )

        result = review_graph.invoke(
            Command(
                resume=[
                    decision.model_dump()
                    for decision in request.decisions
                ]
            ),
            config=config,
        )

        return build_response(thread, result)
