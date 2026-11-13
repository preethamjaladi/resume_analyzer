"""Build and compile the notebook workflow."""

from langgraph.graph import END, START, StateGraph

from .comparison import compare_resume_jd
from .extraction import analyze_jd, analyze_resume
from .schemas import State, HumanReview
from .scoring import calculate_match_score
from .verification import verify_requirements
from langgraph.types import interrupt
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from .human_review import apply_human_review
from .optimization import generate_resume_suggestions
from .edit_proposals import generate_edit_proposals
from .human_review import review_resume_edits
from .patching import apply_resume_edits

workflow_builder = StateGraph(State)

workflow_builder.add_node("analyze_resume", analyze_resume)
workflow_builder.add_node("analyze_jd", analyze_jd)
workflow_builder.add_node("compare_resume_jd", compare_resume_jd)
workflow_builder.add_node("verify_requirements", verify_requirements)
workflow_builder.add_node("calculate_match_score", calculate_match_score)

workflow_builder.add_edge(START, "analyze_resume")
workflow_builder.add_edge("analyze_resume", "analyze_jd")
workflow_builder.add_edge("analyze_jd", "compare_resume_jd")
workflow_builder.add_edge("compare_resume_jd", "verify_requirements")
workflow_builder.add_edge("verify_requirements", "calculate_match_score")
workflow_builder.add_edge("calculate_match_score", END)

workflow_graph = workflow_builder.compile()

def human_review_checkpoint(state: State):
    review_data = interrupt({
        "message": "Review the resume analysis before proceeding.",
        "match_score": state["match_score"],
        "hard_gaps": state["hard_gaps"],
        "requirement_matches": [
            match.model_dump()
            for match in state["requirement_matches"]
        ],
    })

    review = HumanReview.model_validate(review_data)

    return {
        "human_review": review,
        "review_completed": True,
    }

def route_optimization(state: State) -> str:
    if state["human_review"].approved_for_optimization:
        return "generate_suggestions"
    return "end"

review_builder = StateGraph(State)

# Register nodes
review_builder.add_node("analyze_resume", analyze_resume)
review_builder.add_node("analyze_jd", analyze_jd)
review_builder.add_node("compare_resume_jd", compare_resume_jd)
review_builder.add_node("verify_requirements", verify_requirements)
review_builder.add_node("calculate_match_score", calculate_match_score)
review_builder.add_node("human_review", human_review_checkpoint)
review_builder.add_node("apply_human_review", apply_human_review)

# Stage 4D — Reuse deterministic scoring after corrections
review_builder.add_node("recalculate_match_score", calculate_match_score)
review_builder.add_node( "generate_resume_suggestions", generate_resume_suggestions)
review_builder.add_node("generate_edit_proposals",generate_edit_proposals)
review_builder.add_node("review_resume_edits",review_resume_edits)
review_builder.add_node("apply_resume_edits",apply_resume_edits)

# Connect workflow
review_builder.add_edge(START, "analyze_resume")
review_builder.add_edge("analyze_resume", "analyze_jd")
review_builder.add_edge("analyze_jd", "compare_resume_jd")
review_builder.add_edge("compare_resume_jd", "verify_requirements")
review_builder.add_edge("verify_requirements", "calculate_match_score")
review_builder.add_edge("calculate_match_score", "human_review")
review_builder.add_edge("human_review", "apply_human_review")
# Stage 4D — Recalculate score
review_builder.add_edge("apply_human_review", "recalculate_match_score")
review_builder.add_conditional_edges(
    "recalculate_match_score", route_optimization,
    {
        "generate_suggestions": "generate_resume_suggestions",
        "end": END,
    }
)
review_builder.add_edge("generate_resume_suggestions","generate_edit_proposals")
review_builder.add_edge("generate_edit_proposals","review_resume_edits")
review_builder.add_edge("review_resume_edits","apply_resume_edits")
review_builder.add_edge("apply_resume_edits",END)

# Checkpoint serializer
serializer = JsonPlusSerializer(
    allowed_msgpack_modules=[
        ("resume_analyzer.schemas", "ResumeSections"),
        ("resume_analyzer.schemas", "JobDescriptionData"),
        ("resume_analyzer.schemas", "RequirementMatch"),
        ("resume_analyzer.schemas", "VerificationResult"),
        ("resume_analyzer.schemas", "HumanReview"),
        ("resume_analyzer.schemas", "ResumeSuggestion"),
        ("resume_analyzer.schemas", "ResumeSuggestions"),
        ("resume_analyzer.schemas", "ResumeEditProposal"),
        ("resume_analyzer.schemas", "ResumeEditDecision"),
    ]
)

checkpointer = InMemorySaver(serde=serializer)

review_graph = review_builder.compile(
    checkpointer=checkpointer
)
