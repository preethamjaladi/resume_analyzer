"""Data models and workflow state from the resume analyzer notebook."""

from typing import Literal, NotRequired, TypedDict

from pydantic import BaseModel, ConfigDict, Field


class Experience(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company: str
    job_title: str
    start_date: str | None
    end_date: str | None
    responsibilities: list[str]
    technologies: list[str]


class Project(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str
    technologies: list[str]
    achievements: list[str]
    start_date: str | None
    end_date: str | None


class Education(BaseModel):
    model_config = ConfigDict(extra="forbid")

    institution: str
    degree: str
    field_of_study: str
    start_date: str | None
    end_date: str | None
    coursework: list[str]


class ResumeSections(BaseModel):
    model_config = ConfigDict(extra="ignore")

    summary: str
    skills: list[str]
    experience: list[Experience]
    projects: list[Project]
    education: list[Education] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)


class JobRequirement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement_id: str
    description: str

    category: Literal[
        "technical_skill",
        "experience",
        "education",
        "certification",
        "language",
        "responsibility",
        "other"
    ]

    importance: Literal["required", "preferred"]

    is_hard_requirement: bool = False


class JobDescriptionData(BaseModel):
    job_title: str
    company: str | None = None

    responsibilities: list[str] = Field(default_factory=list)

    requirements: list[JobRequirement]


class RequirementMatch(BaseModel):
    requirement_id: str

    status: Literal[
        "met",
        "partially_met",
        "not_met",
        "unknown"
    ]

    evidence: str | None = None

    match_type: Literal[
        "exact",
        "semantic",
        "none"
    ]

    explanation: str


class ComparisonResult(BaseModel):
    requirement_matches: list[RequirementMatch]


class VerificationResult(BaseModel):
    requirement_id: str

    verification_method: Literal[
        "education",
        "experience",
        "explicit_evidence",
        "skill_matching",
        "semantic_review"
    ]

    status: Literal[
        "verified",
        "contradiction",
        "insufficient_evidence",
        "needs_review"
    ]

    explanation: str


class AnalysisResult(BaseModel):
    requirement_matches: list[RequirementMatch]

    match_score: float | None = None

    hard_gaps: list[str] = Field(default_factory=list)

# HUMAN-IN-THE-LOOP REVIEW

class RequirementReview(BaseModel):
    requirement_id: str

    decision: Literal[
        "approve",
        "correct"
    ]

    corrected_status: Literal[
        "met",
        "partially_met",
        "not_met",
        "unknown"
    ] | None = None

    reason: str | None = None


class HumanReview(BaseModel):
    reviews: list[RequirementReview] = Field(
        default_factory=list
    )

    additional_information: list[str] = Field(
        default_factory=list
    )

    approved_for_optimization: bool = False


#RESUME IMPROVEMENT SUGGESTIONS

class ResumeSuggestion(BaseModel):
    requirement_id: str | None = None

    section: Literal[
        "summary",
        "skills",
        "experience",
        "projects",
        "education",
        "certifications",
        "other"
    ]

    action: Literal[
        "add",
        "rewrite",
        "highlight",
        "remove"
    ]

    priority: Literal[
        "high",
        "medium",
        "low"
    ]

    current_text: str | None = None
    suggested_text: str

    reason: str


class ResumeSuggestions(BaseModel):
    suggestions: list[ResumeSuggestion] = Field(
        default_factory=list
    )


# ==========================================
# STAGE 4F — RESUME EDITING & VERSIONING
# ==========================================

class ResumeEditProposal(BaseModel):
    edit_id: str
    requirement_id: str | None = None

    section: str
    operation: Literal["replace", "insert", "delete"]

    # Exact character positions in source resume
    start_index: int
    end_index: int

    original_text: str
    proposed_text: str

    supporting_evidence: list[str] = Field(
        default_factory=list
    )

    reason: str


class ResumeEditDecision(BaseModel):
    edit_id: str

    decision: Literal[
        "accept",
        "edit",
        "reject"
    ]

    edited_text: str | None = None


class ResumeVersion(BaseModel):
    version_id: str
    parent_version_id: str | None = None

    resume_content: str

    applied_edit_ids: list[str] = Field(
        default_factory=list
    )

    match_score: float | None = None
    hard_gaps: list[str] = Field(
        default_factory=list
    )

    faithfulness_passed: bool | None = None


class State(TypedDict):
    # Initial inputs
    resume: str
    job_description: str

    # LLM extraction outputs
    resume_sections: NotRequired[ResumeSections]
    jd_requirements: NotRequired[JobDescriptionData]

    # Comparison output
    requirement_matches: NotRequired[list[RequirementMatch]]

    # Scoring output
    match_score: NotRequired[float]
    hard_gaps: NotRequired[list[str]]

    verification_results: NotRequired[list[VerificationResult]]

    # Stage 4 — Human review
    human_review: NotRequired[HumanReview]
    review_completed: NotRequired[bool]
    # Stage 4 — AI improvement suggestions
    resume_suggestions: NotRequired[ResumeSuggestions]
        # Stage 4F — Resume editing
    edit_proposals: NotRequired[list[ResumeEditProposal]]
    edit_decisions: NotRequired[list[ResumeEditDecision]]
    tailored_resume: NotRequired[str]
    resume_version: NotRequired[ResumeVersion]

    # Final output
    final_report: NotRequired[str]
    

