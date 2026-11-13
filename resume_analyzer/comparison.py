"""Compare every job requirement with resume evidence."""

from .config import structured_compare_llm
from .schemas import State


def compare_resume_jd(state: State):
    resume_sections = state["resume_sections"]
    jd_requirements = state["jd_requirements"]
    original_resume = state["resume"]

    prompt = f"""
    You are an evidence-based resume evaluator.

    Compare the candidate's resume against EVERY job requirement.

    ORIGINAL RESUME:
    {original_resume}

    STRUCTURED RESUME:
    {resume_sections.model_dump_json()}

    JOB REQUIREMENTS:
    {jd_requirements.model_dump_json()}

    INSTRUCTIONS:

    1. Evaluate every requirement individually.
    2. Preserve the requirement_id from the job description.
    3. Return exactly one RequirementMatch per requirement.

    4. Classify the status as:
       - met: Clear evidence satisfies the requirement.
       - partially_met: Related experience exists but does not
         fully satisfy the requirement.
       - not_met: The resume provides no supporting evidence.
       - unknown: The information is insufficient to determine.

    5. Evidence must be an EXACT substring copied from the
       ORIGINAL RESUME.

    6. If no supporting evidence exists, return evidence=null.

    7. Classify match_type:
       - exact: Direct evidence of the requirement.
       - semantic: Related experience or equivalent terminology.
       - none: No supporting evidence.

    8. Do not invent skills, experience, qualifications,
       certifications, or language proficiency.

    9. Using AI coding assistants does not automatically
   demonstrate LLM application development.

   10. Distinguish familiarity from hands-on experience:
      - If the JD asks for familiarity with a technology and
         the resume lists it under SKILLS without demonstrated
         practical usage, classify as partially_met.
      - If the JD asks for hands-on, professional, or production
         experience, a skills-list mention alone is insufficient
         to classify the requirement as met.
      - Do not treat technologies mentioned only in disclaimers,
         keyword lists, unrelated text, or explicit statements
         of non-use as supporting evidence.
      - For partially_met, provide an exact resume quote
         demonstrating the limited evidence.
      - If no credible supporting evidence exists, classify
         as not_met with evidence=null.

   11. Numerical experience requirements are strict:
      - If documented relevant experience is below the
         required duration, classify as not_met.
      - Meeting the duration alone does not prove that the
         experience is relevant.

   12. Explain every judgment briefly.

    Return structured requirement_matches.
    """

    result = structured_compare_llm.invoke(prompt)

    return {
        "requirement_matches": result.requirement_matches
    }
