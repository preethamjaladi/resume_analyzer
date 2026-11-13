
"""FastAPI endpoints for the Resume Analyzer MVP."""

from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from langgraph.types import Command

from .graph import review_graph
from .schemas import RequirementReview, ResumeEditDecision


app = FastAPI(title="Resume Analyzer API")


class AnalysisRequest(BaseModel):
    resume: str = Field(min_length=1)
    job_description: str = Field(min_length=1)


class ReviewRequest(BaseModel):
    reviews: list[RequirementReview] = Field(default_factory=list)
    additional_information: list[str] = Field(default_factory=list)
    approved_for_optimization: bool = False


class EditReviewRequest(BaseModel):
    decisions: list[ResumeEditDecision]


def graph_config(thread_id: str):
    return {"configurable": {"thread_id": thread_id}}


def build_response(thread_id: str, result: dict):
    snapshot = review_graph.get_state(graph_config(thread_id))
    state = snapshot.values

    interrupts = [
        item.value
        for item in result.get("__interrupt__", ())
    ]

    return jsonable_encoder({
        "thread_id": thread_id,
        "status": "paused" if interrupts else "completed",
        "next_nodes": list(snapshot.next),
        "interrupts": interrupts,
        "review_completed": state.get("review_completed", False),
        "match_score": state.get("match_score"),
        "hard_gaps": state.get("hard_gaps", []),
        "requirement_matches": state.get("requirement_matches", []),
        "resume_suggestions": state.get("resume_suggestions"),
        "edit_proposals": state.get("edit_proposals", []),
        "tailored_resume": state.get("tailored_resume"),
    })


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyses")
def start_analysis(request: AnalysisRequest):
    thread_id = str(uuid4())

    result = review_graph.invoke(
        request.model_dump(),
        config=graph_config(thread_id),
    )

    return build_response(thread_id, result)


@app.post("/analyses/{thread_id}/review")
def submit_review(thread_id: str, request: ReviewRequest):
    config = graph_config(thread_id)
    snapshot = review_graph.get_state(config)

    if "human_review" not in snapshot.next:
        raise HTTPException(
            status_code=409,
            detail="Analysis is not waiting for human review.",
        )

    result = review_graph.invoke(
        Command(resume=request.model_dump()),
        config=config,
    )

    return build_response(thread_id, result)


@app.post("/analyses/{thread_id}/edits")
def submit_edit_decisions(thread_id: str, request: EditReviewRequest):
    config = graph_config(thread_id)
    snapshot = review_graph.get_state(config)

    if "review_resume_edits" not in snapshot.next:
        raise HTTPException(
            status_code=409,
            detail="Analysis is not waiting for edit decisions.",
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

    return build_response(thread_id, result)
