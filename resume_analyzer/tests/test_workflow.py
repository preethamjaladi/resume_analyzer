"""Notebook samples and offline workflow validation.

Run: python -m unittest discover -s resume_analyzer/tests -v
"""

import unittest
from unittest.mock import Mock, patch

from resume_analyzer.graph import workflow_graph
from resume_analyzer.schemas import (
    ComparisonResult, JobDescriptionData, JobRequirement, RequirementMatch,
    ResumeSections, State,
)
from resume_analyzer.scoring import calculate_match_score
from resume_analyzer.verification import verify_requirements


resume_test_state = {
    "resume": """
John Doe

Summary
Software Engineer with experience building backend and full-stack applications using Python, Java, Flask, React, and PostgreSQL.

SKILLS
Python, Java, JavaScript, React, Flask, PostgreSQL, Git, Docker, REST APIs

EXPERIENCE
Software Developer Intern | ABC Tech | Jan 2025 - May 2025
- Built REST APIs using Flask and PostgreSQL
- Developed frontend components using React
- Used Git and Docker for development and deployment
- Improved API response time by optimizing database queries

PROJECTS
Job Tracker Application | 2025
- Built using Python, Flask, PostgreSQL, HTML, CSS, and JavaScript
- Created CRUD functionality for managing job applications

EDUCATION
B.S. in Computer Science
XYZ University | 2021 - 2025
Relevant Coursework: Data Structures and Algorithms, Operating Systems, Database Systems, Computer Networks
""",

    "job_description": """
Looking for a Junior Software Engineer with experience in Python, REST APIs, PostgreSQL, Docker, and cloud technologies.
Experience with React and Git is preferred.
"""

}


jd_test_state = {
    "resume": "",
    "job_description": """
Software Engineer

Responsibilities:
- Develop and maintain backend services and REST APIs
- Collaborate with frontend engineers and product teams
- Write clean, testable, maintainable code
- Participate in code reviews and debugging

Basic Qualifications:
- Bachelor's degree in Computer Science or related field
- Strong understanding of data structures and algorithms
- Familiarity with software development best practices

Required Skills:
- Python
- SQL
- REST APIs
- Git
- PostgreSQL
- Docker

Experience Requirements:
- 1+ years of software development experience
- Experience building backend applications
- Experience working with relational databases

"""
}


jd_test_state_2 = {
    "job_description": """
    AI Engineer Intern
    

    Responsibilities:
    - Develop AI agents using large language models.
    - Build automated workflows using LangGraph.
    - Integrate AI applications with REST APIs and databases.

    Required Qualifications:
    - Master's degree in Computer Science or related field.
    - Proficiency in Python.
    - Experience with LLM application development.
    - Experience with LangGraph and tool calling.
    - Fluency in Mandarin Chinese and English.

    Preferred Qualifications:
    - Experience with AWS.
    - Familiarity with Docker.
    - Knowledge of retrieval-augmented generation (RAG).
    """
}


def run_validation(state: State):
    """Consolidate the notebook's deterministic integration checks."""
    validated_state = state.copy()
    requirements = validated_state["jd_requirements"].requirements
    jd_ids = [req.requirement_id for req in requirements]
    match_ids = [match.requirement_id for match in state["requirement_matches"]]

    assert len(jd_ids) == len(set(jd_ids)), "Duplicate requirement IDs"
    assert len(match_ids) == len(set(match_ids)), "Duplicate matches"
    assert set(match_ids) == set(jd_ids), "Missing or extra requirements"

    validated_state.update(verify_requirements(validated_state))
    validated_state.update(calculate_match_score(validated_state))
    verification_ids = [
        result.requirement_id for result in validated_state["verification_results"]
    ]
    assert len(verification_ids) == len(set(verification_ids)), "Duplicate verifications"
    assert set(verification_ids) == set(jd_ids), "Missing or extra verifications"
    assert 0 <= validated_state["match_score"] <= 100, "Score outside valid range"
    return validated_state


def sample_state() -> State:
    """Use fixed extraction outputs so validation needs no Groq calls."""
    return {
        **resume_test_state,
        "resume_sections": ResumeSections(
            summary="Software Engineer", skills=["Python", "Docker"],
            experience=[], projects=[], education=[], certifications=[],
            languages=[], links=[],
        ),
        "jd_requirements": JobDescriptionData(
            job_title="Junior Software Engineer",
            requirements=[
                JobRequirement(
                    requirement_id="REQ_001", description="Python",
                    category="technical_skill", importance="required",
                ),
                JobRequirement(
                    requirement_id="REQ_002", description="AWS",
                    category="technical_skill", importance="preferred",
                    is_hard_requirement=True,
                ),
            ],
        ),
        "requirement_matches": [
            RequirementMatch(
                requirement_id="REQ_001", status="met", evidence="Python",
                match_type="exact", explanation="Python is listed in the resume.",
            ),
            RequirementMatch(
                requirement_id="REQ_002", status="not_met", evidence=None,
                match_type="none", explanation="AWS is not documented.",
            ),
        ],
    }


class WorkflowTests(unittest.TestCase):
    def test_validation_and_weighted_score(self):
        result = run_validation(sample_state())
        self.assertEqual(result["match_score"], 75.0)
        self.assertEqual(result["hard_gaps"], ["AWS"])
        self.assertTrue(all(
            item.status == "verified" for item in result["verification_results"]
        ))

    def test_invalid_evidence_receives_no_credit(self):
        state = sample_state()
        state["requirement_matches"][0] = state["requirement_matches"][0].model_copy(
            update={"evidence": "An invented Python quotation"}
        )
        result = run_validation(state)
        self.assertEqual(result["match_score"], 0.0)
        self.assertEqual(result["requirement_matches"][0].status, "unknown")
        self.assertEqual(result["verification_results"][0].status, "contradiction")

    def test_validation_rejects_duplicate_or_missing_matches(self):
        for matches in [[], [sample_state()["requirement_matches"][0]] * 2]:
            with self.subTest(matches=matches), self.assertRaises(AssertionError):
                state = sample_state()
                state["requirement_matches"] = matches
                run_validation(state)

    def test_compiled_graph_with_mocked_llms(self):
        state = sample_state()
        resume_model = Mock()
        resume_model.invoke.return_value = state["resume_sections"]
        jd_model = Mock()
        jd_model.invoke.return_value = state["jd_requirements"]
        comparison_model = Mock()
        comparison_model.invoke.return_value = ComparisonResult(
            requirement_matches=state["requirement_matches"]
        )
        with (
            patch("resume_analyzer.extraction.resume_llm", resume_model),
            patch("resume_analyzer.extraction.jd_llm", jd_model),
            patch("resume_analyzer.comparison.structured_compare_llm", comparison_model),
        ):
            result = workflow_graph.invoke({
                "resume": state["resume"],
                "job_description": state["job_description"],
            })
        self.assertEqual(result["match_score"], 75.0)
        self.assertEqual(len(result["verification_results"]), 2)
        for model in (resume_model, jd_model, comparison_model):
            model.invoke.assert_called_once()


if __name__ == "__main__":
    unittest.main()
