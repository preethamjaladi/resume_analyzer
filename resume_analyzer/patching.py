
"""Apply user-approved resume edits deterministically."""

from .schemas import State


def apply_resume_edits(state: State) -> dict:
    """Build a tailored resume without modifying the original."""

    original = state["resume"]
    proposals = state["edit_proposals"]
    decisions = state["edit_decisions"]

    proposal_lookup = {
        proposal.edit_id: proposal
        for proposal in proposals
    }

    accepted_edits = []

    for decision in decisions:
        if decision.decision == "reject":
            continue

        proposal = proposal_lookup.get(decision.edit_id)

        if proposal is None:
            raise ValueError(
                f"Unknown edit ID: {decision.edit_id}"
            )

        if proposal.operation != "replace":
            raise ValueError(
                f"Unsupported operation: {proposal.operation}"
            )

        replacement = (
            decision.edited_text
            if decision.decision == "edit"
            else proposal.proposed_text
        )

        if replacement is None:
            raise ValueError(
                f"Missing replacement text for {decision.edit_id}"
            )

        start = proposal.start_index
        end = proposal.end_index

        if original[start:end] != proposal.original_text:
            raise ValueError(
                f"Source text mismatch for {decision.edit_id}"
            )

        accepted_edits.append(
            (start, end, replacement)
        )

    # Sort edits by source position
    accepted_edits.sort(key=lambda edit: edit[0])

    # Detect overlapping edits
    for index in range(1, len(accepted_edits)):
        previous_end = accepted_edits[index - 1][1]
        current_start = accepted_edits[index][0]

        if current_start < previous_end:
            raise ValueError(
                "Overlapping resume edits detected"
            )

    # Apply from right to left to preserve offsets
    tailored = original

    for start, end, replacement in reversed(accepted_edits):
        tailored = (
            tailored[:start]
            + replacement
            + tailored[end:]
        )

    return {"tailored_resume": tailored}
