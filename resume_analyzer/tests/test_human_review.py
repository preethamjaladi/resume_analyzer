
from langgraph.types import Command

from resume_analyzer.graph import review_graph
from resume_analyzer.schemas import ResumeSuggestions
from resume_analyzer.edit_proposals import generate_edit_proposals

# Unique thread ID for this test
config = {"configurable": {"thread_id": "stage4-test-001"}}

# ==========================================
# TEST DATA
# ==========================================

resume = """
Python developer with experience building FastAPI applications.
"""

job_description = """
Required Qualifications:
- Proficiency in Python.
- Experience building REST APIs using FastAPI.
"""

# ==========================================
# TEST 1 — RUN WORKFLOW UNTIL INTERRUPT
# ==========================================

result = review_graph.invoke(
    {
        "resume": resume,
        "job_description": """
                            Position: Backend Python Developer

                            Minimum Qualifications:
                            - Must have proficiency in Python.
                            - Must have experience developing REST APIs using FastAPI.

                            Strict Eligibility Requirements:
                            - Python proficiency is a non-negotiable requirement.
                            - Candidates without Python proficiency are ineligible.
                            """,
    },
    config=config,
)

assert "__interrupt__" in result
print("\n--- REQUIREMENT DEBUG ---")

for req in result["jd_requirements"].requirements:
    match = next(
        m for m in result["requirement_matches"]
        if m.requirement_id == req.requirement_id
    )

    print(
        "ID:", req.requirement_id,
        "| Importance:", req.importance,
        "| Hard:", req.is_hard_requirement,
        "| Status:", match.status
    )

# Find a hard requirement initially classified as met
hard_requirement = next(
    (
        req
        for req in result["jd_requirements"].requirements
        if req.is_hard_requirement
        and any(
            match.requirement_id == req.requirement_id
            and match.status == "met"
            for match in result["requirement_matches"]
        )
    ),
    None,
)

assert hard_requirement is not None, (
    "Test requires a hard requirement initially classified as met"
)

target_id = hard_requirement.requirement_id
target_description = hard_requirement.description

original_match = next(
    match
    for match in result["requirement_matches"]
    if match.requirement_id == target_id
)

original_status = original_match.status
original_score = result["match_score"]
original_hard_gaps = result["hard_gaps"].copy()

print("Testing requirement:", target_id)
print("Requirement:", target_description)
print("Original status:", original_status)
print("Original score:", original_score)
print("PASS: Workflow paused for human review")


# ==========================================
# TEST 2 — RESUME WITH USER CORRECTION
# ==========================================

result = review_graph.invoke(
    Command(
        resume={
            "reviews": [
                {
                    "requirement_id": target_id,
                    "decision": "correct",
                    "corrected_status": "not_met",
                }
            ],
            "approved_for_optimization": False,
        }
    ),
    config=config,
)

# Verify graph completed
snapshot = review_graph.get_state(config)

assert snapshot.next == (), (
    f"Workflow did not finish. Pending nodes: {snapshot.next}"
)

# Verify human review was stored
assert result["review_completed"] is True

assert (
    result["human_review"].reviews[0].requirement_id
    == target_id
)

assert (
    result["human_review"].reviews[0].corrected_status
    == "not_met"
)

print("PASS: Human review stored successfully")


# ==========================================
# TEST 3 — VERIFY CORRECTION WAS APPLIED
# ==========================================

corrected_match = next(
    match
    for match in result["requirement_matches"]
    if match.requirement_id == target_id
)

corrected_status = corrected_match.status

print("Corrected status:", corrected_status)

assert corrected_status == "not_met"

assert original_status != corrected_status, (
    "Correction failed: original and corrected "
    "statuses are identical."
)

print("PASS: User correction applied successfully")


# ==========================================
# TEST 4 — VERIFY DETERMINISTIC RESCORING
# ==========================================

updated_score = result["match_score"]
updated_hard_gaps = result["hard_gaps"]

print("Original score:", original_score)
print("Updated score:", updated_score)

assert updated_score < original_score, (
    "Score did not decrease after changing "
    "a met requirement to not_met."
)

print("PASS: Match score recalculated successfully")


# ==========================================
# TEST 5 — VERIFY HARD GAP UPDATE
# ==========================================

print("Original hard gaps:", original_hard_gaps)
print("Updated hard gaps:", updated_hard_gaps)

assert target_description not in original_hard_gaps, (
    "Target requirement was already a hard gap "
    "before correction."
)

assert target_description in updated_hard_gaps, (
    f"Hard requirement {target_id} was not "
    "added to hard_gaps."
)

print("PASS: Hard gap updated successfully")


# ==========================================
# FINAL RESULT
# ==========================================

print("\nStage 4D human review and rescoring tests passed")

# ==========================================
# TEST 6 — OPTIMIZATION ENABLED
# ==========================================

from resume_analyzer.schemas import ResumeSuggestions

# TEST 6 — OPTIMIZATION DISABLED

assert "resume_suggestions" not in result, (
    "Suggestions were generated despite optimization being disabled"
)

print("PASS: Optimization correctly skipped")

# ==========================================
# TEST 7 — EDIT PROPOSAL GENERATION
# ==========================================

proposal_result = generate_edit_proposals(result)
proposals = proposal_result["edit_proposals"]

print("\n--- EDIT PROPOSALS ---")
print("Proposals generated:", len(proposals))

for proposal in proposals:
    assert (
        resume[proposal.start_index:proposal.end_index]
        == proposal.original_text
    ), f"Invalid source position: {proposal.edit_id}"

    assert proposal.operation == "replace"
    assert proposal.supporting_evidence

    print("Edit ID:", proposal.edit_id)
    print("Requirement:", proposal.requirement_id)
    print("Original:", proposal.original_text)
    print("Proposed:", proposal.proposed_text)
    print("Evidence:", proposal.supporting_evidence)
    print("---")

print("PASS: Edit proposal positions validated")