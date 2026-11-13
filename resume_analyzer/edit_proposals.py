
"""Generate structured, evidence-linked resume edit proposals."""

from .config import llm
from uuid import uuid4
from .schemas import ResumeEditProposal, ResumeSuggestions


def generate_edit_proposals(state):
    resume = state["resume"]
    suggestions_data = state.get("resume_suggestions")

    if suggestions_data is None:
        return {"edit_proposals": []}

    # Support either Pydantic objects or dictionaries.
    suggestions = (
        ResumeSuggestions.model_validate(suggestions_data)
        .suggestions
    )

    proposals = []
    used_ranges = []

    for suggestion in suggestions:
        # MVP patching currently supports replacement only.
        if suggestion.action != "rewrite":
            continue

        original = suggestion.current_text
        replacement = suggestion.suggested_text

        if not original or not replacement:
            continue

        # Require the original text to appear exactly once.
        # This prevents accidental replacements.
        if resume.count(original) != 1:
            continue

        if original == replacement:
            continue

        start = resume.index(original)
        end = start + len(original)

        # Prevent overlapping proposed edits.
        if any(
            start < used_end and end > used_start
            for used_start, used_end in used_ranges
        ):
            continue

        used_ranges.append((start, end))

        proposals.append(
            ResumeEditProposal(
                edit_id=f"EDIT_{len(proposals) + 1:03d}",
                requirement_id=suggestion.requirement_id,
                section=suggestion.section,
                operation="replace",
                start_index=start,
                end_index=end,
                original_text=original,
                proposed_text=replacement,
                supporting_evidence=[original],
                reason=suggestion.reason,
            )
        )

    return {"edit_proposals": proposals}
