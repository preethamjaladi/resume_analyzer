
"""Test human edit approval and patching through LangGraph."""

from uuid import uuid4

from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

from resume_analyzer.schemas import (
    State,
    ResumeEditProposal,
)
from resume_analyzer.human_review import review_resume_edits
from resume_analyzer.patching import apply_resume_edits


# ==========================================
# TEST GRAPH — REAL APPLICATION NODES
# ==========================================

builder = StateGraph(State)

builder.add_node("review_resume_edits", review_resume_edits)
builder.add_node("apply_resume_edits", apply_resume_edits)

builder.add_edge(START, "review_resume_edits")
builder.add_edge("review_resume_edits", "apply_resume_edits")
builder.add_edge("apply_resume_edits", END)

serializer = JsonPlusSerializer(
    allowed_msgpack_modules=[
        ("resume_analyzer.schemas", "ResumeEditProposal"),
        ("resume_analyzer.schemas", "ResumeEditDecision"),
    ]
)

test_graph = builder.compile(
    checkpointer=InMemorySaver(serde=serializer)
)


# ==========================================
# TEST DATA
# ==========================================

original_resume = (
    "SUMMARY\n"
    "Python developer.\n"
    "EXPERIENCE\n"
    "Built REST APIs.\n"
)

original_text = "Built REST APIs."
proposed_text = "Developed REST APIs."

start = original_resume.index(original_text)

proposal = ResumeEditProposal(
    edit_id="EDIT_001",
    requirement_id="REQ_001",
    section="experience",
    operation="replace",
    start_index=start,
    end_index=start + len(original_text),
    original_text=original_text,
    proposed_text=proposed_text,
    supporting_evidence=[original_text],
    reason="Improve action verb.",
)


# ==========================================
# TEST ALL THREE USER DECISIONS
# ==========================================

test_cases = [
    (
        "accept",
        None,
        "Developed REST APIs."
    ),
    (
        "edit",
        "Implemented backend REST APIs.",
        "Implemented backend REST APIs."
    ),
    (
        "reject",
        None,
        "Built REST APIs."
    ),
]

for decision, edited_text, expected_text in test_cases:

    config = {
        "configurable": {
            "thread_id": f"patch-test-{uuid4().hex}"
        }
    }

    # Start workflow and pause for human review
    result = test_graph.invoke(
        {
            "resume": original_resume,
            "edit_proposals": [proposal],
        },
        config=config,
    )

    assert "__interrupt__" in result
    print(f"PASS: {decision} checkpoint reached")

    # Resume with user decision
    result = test_graph.invoke(
        Command(
            resume=[
                {
                    "edit_id": "EDIT_001",
                    "decision": decision,
                    "edited_text": edited_text,
                }
            ]
        ),
        config=config,
    )

    # Confirm the workflow finished
    assert test_graph.get_state(config).next == ()

    # Confirm the correct wording
    assert expected_text in result["tailored_resume"]

    # Confirm the original was preserved
    assert result["resume"] == original_resume

    # Confirm the saved decision
    assert result["edit_decisions"][0].decision == decision

    # Verify the entire resulting resume
    expected_resume = original_resume.replace(
        original_text,
        expected_text,
        1,
    )

    assert result["tailored_resume"] == expected_resume

    print(f"PASS: {decision} operation applied correctly")


print("\nStage 4F.4 LangGraph patch integration tests passed")
