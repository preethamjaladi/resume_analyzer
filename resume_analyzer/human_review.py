from .schemas import State
from langgraph.types import interrupt
from .schemas import ResumeEditDecision

def apply_human_review(state: State) -> dict:
    review = state["human_review"]
    matches = state["requirement_matches"]

    corrections = {
        item.requirement_id: item
        for item in review.reviews
        if item.decision == "correct"
    }

    updated_matches = []

    for match in matches:
        correction = corrections.get(match.requirement_id)

        if correction is None:
            updated_matches.append(match)
            continue

        if correction.corrected_status is None:
            raise ValueError(
                f"Missing corrected_status for {match.requirement_id}"
            )

        updated_matches.append(
            match.model_copy(
                update={
                    "status": correction.corrected_status,
                    "explanation": (
                        correction.reason
                        or "Classification corrected by user."
                    ),
                }
            )
        )

    return {"requirement_matches": updated_matches}


def review_resume_edits(state: State) -> dict:
    """Pause for user decisions on individual resume edits."""

    proposals = state["edit_proposals"]

    # No proposals means nothing needs approval
    if not proposals:
        return {"edit_decisions": []}

    response = interrupt({
        "message": "Review the proposed resume edits.",
        "proposals": [
            proposal.model_dump()
            for proposal in proposals
        ],
    })

    # Validate the submitted decisions
    decisions = [
        ResumeEditDecision.model_validate(item)
        for item in response
    ]

    proposal_ids = [p.edit_id for p in proposals]
    decision_ids = [d.edit_id for d in decisions]

    # Every proposal must receive exactly one decision
    if (
        len(decision_ids) != len(proposal_ids)
        or set(decision_ids) != set(proposal_ids)
    ):
        raise ValueError(
            "Each proposal must receive exactly one decision."
        )

    # Edited proposals must provide replacement text
    for decision in decisions:
        if (
            decision.decision == "edit"
            and decision.edited_text is None
        ):
            raise ValueError(
                f"Missing edited_text for {decision.edit_id}"
            )

    return {"edit_decisions": decisions}
