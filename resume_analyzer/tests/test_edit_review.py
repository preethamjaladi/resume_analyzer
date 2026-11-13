
"""Test the human edit-review checkpoint."""

from uuid import uuid4

from langgraph.types import Command

from resume_analyzer.graph import review_graph

config = {
    "configurable": {
        "thread_id": f"edit-review-{uuid4().hex}"
    }
}

resume = """
Python developer with experience building FastAPI applications.
"""

job_description = """
Backend Python Developer

Required Qualifications:
- Proficiency in Python.
- Experience developing REST APIs using FastAPI.
"""

# TEST 1 — Run initial analysis
result = review_graph.invoke(
    {
        "resume": resume,
        "job_description": job_description,
    },
    config=config,
)

assert "__interrupt__" in result
print("PASS: Initial human review checkpoint reached")

# TEST 2 — Approve analysis and enable optimization
result = review_graph.invoke(
    Command(
        resume={
            "reviews": [],
            "additional_information": [],
            "approved_for_optimization": True,
        }
    ),
    config=config,
)

assert result["review_completed"] is True
assert result["human_review"].approved_for_optimization is True

proposals = result.get("edit_proposals", [])

print("Suggestions:", len(result["resume_suggestions"].suggestions))

for suggestion in result["resume_suggestions"].suggestions:
    print(
        "Action:", suggestion.action,
        "| Current:", repr(suggestion.current_text)
    )
print("Edit proposals generated:", len(proposals))

# TEST 3 — Review proposed edits
if proposals:
    assert "__interrupt__" in result, (
        "Expected edit-review interrupt when proposals exist"
    )

    decisions = [
        {
            "edit_id": proposal.edit_id,
            "decision": "accept",
        }
        for proposal in proposals
    ]

    # Resume from the second interrupt
    result = review_graph.invoke(
        Command(resume=decisions),
        config=config,
    )

    assert len(result["edit_decisions"]) == len(proposals)
    assert all(
        decision.decision == "accept"
        for decision in result["edit_decisions"]
    )

    print("PASS: Edit decisions stored successfully")
else:
    assert "__interrupt__" not in result
    print("PASS: No edit proposals; review skipped")
# ==========================================
# TEST 4 — VERIFY ORIGINAL & TAILORED RESUME
# ==========================================

assert result["resume"] == resume

assert review_graph.get_state(config).next == ()

assert "tailored_resume" in result

if proposals:
    # All proposals were accepted in this test.
    # The tailored resume should contain approved changes.
    assert result["tailored_resume"] != resume, (
        "Accepted edits were not applied to the tailored resume"
    )

    print("PASS: Accepted edits applied to tailored resume")

else:
    # No proposals means no modifications.
    assert result["tailored_resume"] == resume

    print("PASS: Empty proposals preserve original resume")

print("PASS: Original resume preserved")
print("Stage 4F.4 LangGraph patch integration test passed")