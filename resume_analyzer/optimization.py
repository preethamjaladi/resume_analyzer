
"""Generate JD-specific resume improvement suggestions."""

from .config import llm
from .schemas import State, ResumeSuggestions


# Use the existing Groq model with structured output
suggestion_llm = llm.with_structured_output(
    ResumeSuggestions,
    method="json_schema",
    strict=True,
)


def generate_resume_suggestions(state: State) -> dict:
    """Generate suggestions using human-reviewed analysis."""

    review = state["human_review"]
    human_corrections = [
    {
        "requirement_id": item.requirement_id,
        "decision": item.decision,
        "corrected_status": item.corrected_status,
        "reason": item.reason,
    }
    for item in review.reviews
]

    # Read the corrected requirement matches
    requirements = state["jd_requirements"].requirements
    matches = state["requirement_matches"]

    requirement_details = [
        {
            "requirement_id": req.requirement_id,
            "description": req.description,
            "importance": req.importance,
            "is_hard_requirement": req.is_hard_requirement,
            "status": next(
                match.status
                for match in matches
                if match.requirement_id == req.requirement_id
            ),
        }
        for req in requirements
    ]

    
    prompt = f"""
            You are an expert technical resume optimization assistant.

            Your task is to recommend accurate, JD-specific improvements
            to a candidate's resume.

            ORIGINAL RESUME:
            {state["resume"]}

            JOB DESCRIPTION:
            {state["job_description"]}

            FINAL HUMAN-REVIEWED REQUIREMENT MATCHES:
            {requirement_details}

            EXPLICIT HUMAN REVIEW DECISIONS:
            {human_corrections}

            UPDATED MATCH SCORE:
            {state["match_score"]}

            HARD GAPS:
            {state["hard_gaps"]}

            ADDITIONAL USER-PROVIDED INFORMATION:
            {review.additional_information}

            STRICT RULES:

            1. Human corrections are authoritative.
            Never override or contradict a user's corrected classification.

            2. Treat all additional information provided by the user
            as true. No further evidence verification is required.

            3. For requirements classified as "met":
            Recommend improvements to clarity, presentation,
            keyword alignment, or impact without inventing facts.

            4. For requirements classified as "partially_met":
            Suggest improvements only for qualifications already
            established by the resume or user-provided information.

            5. For requirements classified as "not_met":
            Do not suggest wording that claims the candidate
            possesses the missing qualification.
            Do not try to satisfy the requirement through
            keyword insertion or exaggerated wording.
            You may recommend making the existing genuine
            experience more relevant without claiming the gap is met.

            6. For requirements classified as "unknown":
            Do not assume the candidate possesses the qualification.

            7. Never invent employers, degrees, certifications,
            skills, technologies, years of experience,
            responsibilities, achievements, or numerical metrics.

            8. Avoid unsupported adjectives such as:
            "expert", "proven", "exceptional", or "robust".

            9. Every suggested_text must be supported by the
            original resume or additional user-provided information.

            10. For rewrite or remove actions, current_text must
                accurately reference existing resume content.

            11. Use exact requirement IDs when a suggestion
                relates to a specific JD requirement.

            12. Prioritize high-value improvements for the target role.
                Do not create suggestions merely to fill the output.

            13. Return structured output matching ResumeSuggestions.

            14. Do not generate suggestions targeting requirements
                explicitly corrected to "not_met" by the user.
                These requirements represent acknowledged gaps.
                Focus recommendations on met or partially_met
                requirements instead.

            15. Every suggestion must provide a meaningful improvement
                in clarity, specificity, relevance, or presentation.
                Avoid trivial paraphrasing of existing resume text.
            """

    suggestions = suggestion_llm.invoke(prompt)

    return {
        "resume_suggestions": suggestions
    }
