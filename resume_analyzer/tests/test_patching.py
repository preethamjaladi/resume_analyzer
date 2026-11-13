
"""Test deterministic resume patch application."""

from resume_analyzer.patching import apply_resume_edits
from resume_analyzer.schemas import (
    ResumeEditProposal,
    ResumeEditDecision,
)

# ==========================================
# TEST DATA
# ==========================================

original_resume = (
    "SUMMARY\n"
    "Python developer.\n"
    "EXPERIENCE\n"
    "Built REST APIs.\n"
    "Used PostgreSQL.\n"
)


def make_proposal(edit_id, original_text, proposed_text):
    start = original_resume.index(original_text)

    return ResumeEditProposal(
        edit_id=edit_id,
        section="experience",
        operation="replace",
        start_index=start,
        end_index=start + len(original_text),
        original_text=original_text,
        proposed_text=proposed_text,
        supporting_evidence=[original_text],
        reason="Improve wording.",
    )


proposals = [
    make_proposal(
        "EDIT_001",
        "Python developer.",
        "Python and FastAPI developer.",
    ),
    make_proposal(
        "EDIT_002",
        "Built REST APIs.",
        "Developed REST APIs.",
    ),
    make_proposal(
        "EDIT_003",
        "Used PostgreSQL.",
        "Worked with PostgreSQL.",
    ),
]

# ==========================================
# TEST 1 — ACCEPT / EDIT / REJECT
# ==========================================

state = {
    "resume": original_resume,
    "edit_proposals": proposals,
    "edit_decisions": [
        ResumeEditDecision(
            edit_id="EDIT_001",
            decision="accept",
        ),
        ResumeEditDecision(
            edit_id="EDIT_002",
            decision="edit",
            edited_text="Developed backend REST APIs.",
        ),
        ResumeEditDecision(
            edit_id="EDIT_003",
            decision="reject",
        ),
    ],
}

result = apply_resume_edits(state)

expected = (
    "SUMMARY\n"
    "Python and FastAPI developer.\n"
    "EXPERIENCE\n"
    "Developed backend REST APIs.\n"
    "Used PostgreSQL.\n"
)

assert result["tailored_resume"] == expected
assert state["resume"] == original_resume

print("PASS: Accepted edit applied")
print("PASS: User-modified edit applied")
print("PASS: Rejected edit ignored")
print("PASS: Original resume preserved")


# ==========================================
# TEST 2 — ALL EDITS REJECTED
# ==========================================

state["edit_decisions"] = [
    ResumeEditDecision(
        edit_id=p.edit_id,
        decision="reject",
    )
    for p in proposals
]

result = apply_resume_edits(state)

assert result["tailored_resume"] == original_resume

print("PASS: All rejected edits preserve original resume")


# ==========================================
# TEST 3 — INVALID SOURCE POSITION
# ==========================================

bad_proposal = make_proposal(
    "EDIT_004",
    "Built REST APIs.",
    "Developed REST APIs.",
)

bad_proposal.start_index = 0

state["edit_proposals"] = [bad_proposal]
state["edit_decisions"] = [
    ResumeEditDecision(
        edit_id="EDIT_004",
        decision="accept",
    )
]

try:
    apply_resume_edits(state)
    raise AssertionError("Invalid source position was accepted")
except ValueError as exc:
    assert "Source text mismatch" in str(exc)

print("PASS: Invalid source position rejected")

print("\nStage 4F.4 patch engine tests passed")

# ==========================================
# TEST 4 — OVERLAPPING EDITS
# ==========================================

overlap_proposals = [
    make_proposal(
        "EDIT_005",
        "Built REST APIs.",
        "Developed REST APIs.",
    ),
    make_proposal(
        "EDIT_006",
        "REST APIs.",
        "backend APIs.",
    ),
]

state["edit_proposals"] = overlap_proposals
state["edit_decisions"] = [
    ResumeEditDecision(edit_id=p.edit_id, decision="accept")
    for p in overlap_proposals
]

try:
    apply_resume_edits(state)
    raise AssertionError("Overlapping edits were accepted")
except ValueError as exc:
    assert "Overlapping resume edits" in str(exc)

print("PASS: Overlapping edits rejected")


# ==========================================
# TEST 5 — UNKNOWN EDIT ID
# ==========================================

state["edit_proposals"] = [proposals[0]]
state["edit_decisions"] = [
    ResumeEditDecision(
        edit_id="EDIT_UNKNOWN",
        decision="accept",
    )
]

try:
    apply_resume_edits(state)
    raise AssertionError("Unknown edit ID was accepted")
except ValueError as exc:
    assert "Unknown edit ID" in str(exc)

print("PASS: Unknown edit ID rejected")
