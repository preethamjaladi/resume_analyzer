"""Extract structured resume and job description data."""

from .config import resume_llm, jd_llm
from .schemas import State
import re

def analyze_resume(state: State):
    resume = state["resume"]

    prompt = f"""
    Extract information from the following resume.

    The resume can have any layout, headings, or section order.
    Identify information based on meaning, not formatting.

    Follow the provided output schema exactly.

    Rules:
    - Preserve factual information.
    - Do not invent missing details.
    - Use empty lists for absent collections.
    - Use null for unavailable dates.
    - Use empty strings for missing required text.
    - Preserve experience responsibilities and achievements.
    - Extract technologies only when supported by the resume.
    - Do not infer language proficiency from the resume's language.

    Resume:
    {resume}
    """

    result = resume_llm.invoke(prompt)

    return {"resume_sections": result}

def count_explicit_requirements(job_description: str):
    counts = {"required": 0, "preferred": 0}
    current_section = None

    for line in job_description.splitlines():
        line = line.strip()
        heading = line.lower().rstrip(":")

        if heading in (
            "required qualifications",
            "minimum qualifications",
            "requirements",
            "must have",
        ):
            current_section = "required"
            continue

        if heading in (
            "preferred qualifications",
            "nice to have",
            "bonus qualifications",
        ):
            current_section = "preferred"
            continue

        if current_section and re.match(r"^[-*]\s+\S", line):
            counts[current_section] += 1

    return counts

def extract_jd_bullets(job_description: str):
    requirements = []
    importance = None

    required_headings = {
        "required qualifications",
        "minimum qualifications",
        "requirements",
        "must have",
    }

    preferred_headings = {
        "preferred qualifications",
        "nice to have",
        "bonus qualifications",
    }

    for line in job_description.splitlines():
        line = line.strip()
        heading = line.lower().rstrip(":")

        if heading in required_headings:
            importance = "required"
            continue

        if heading in preferred_headings:
            importance = "preferred"
            continue

        if importance and line.startswith(("-", "*")):
            description = line[1:].strip()

            if description:
                requirements.append({
                    "description": description,
                    "importance": importance
                })

    return requirements

def analyze_jd(state: State):
    job_description = state["job_description"]

    explicit_requirements = extract_jd_bullets(job_description)
    bullet_context = "\n".join(
        f"- [{item['importance'].upper()}] {item['description']}"
        for item in explicit_requirements
    )

    prompt = f"""
      You are a job description analysis system.

      Extract structured information from the job description,
      regardless of its formatting, headings, or organization.

      Identify:
      1. Job title and company
      2. Responsibilities
      3. Technical skills
      4. Experience requirements
      5. Education requirements
      6. Certifications
      7. Language requirements
      8. Other qualifications

      For EVERY requirement:
      - Assign a unique ID: REQ_001, REQ_002, etc.
      - Preserve the original meaning.
      - Classify its category.
      - Mark importance as "required" or "preferred".
      - Set is_hard_requirement=True only when the JD
        explicitly indicates a mandatory qualification.
      - Do not automatically consider every required skill
        a hard requirement.

      REQUIREMENT EXTRACTION RULES:
      - Extract EVERY explicitly stated qualification.
      - Include both REQUIRED and PREFERRED qualifications.
      - Never omit a qualification because it is unrelated
        to the job title or other requirements.
      - Treat each distinct qualification as a separate requirement.
      - Do not merge unrelated qualifications.
      - Preserve the order of requirements in the JD.
      - Do not invent additional requirements.

      IMPORTANCE CLASSIFICATION:
      - Qualifications under "Required", "Minimum", or
        "Must Have" sections are required.
      - Qualifications under "Preferred", "Nice to Have",
        or "Bonus" sections are preferred.
      - A section heading applies to every qualification
        listed beneath it until another section begins.
      - Do not change importance based on how relevant
        a skill seems to the job title.
      - For qualifications outside explicit sections,
        determine importance from the wording.

      HARD REQUIREMENT CLASSIFICATION:
      - Set is_hard_requirement=True only when the JD
        explicitly uses mandatory, must, non-negotiable,
        or equivalent language for that qualification.
      - Do not infer hard requirements from the job title.
      - Being listed under Required does not automatically
        mean is_hard_requirement=True.

      COMPLETENESS CHECK:
      Before returning the result:
      1. Identify every explicitly stated qualification.
      2. Check that each appears in the requirements list.
      3. Verify that required qualifications remain required.
      4. Verify that preferred qualifications remain preferred.
      5. Check that requirement IDs are unique and sequential.
      6. Ensure no qualifications were invented.

      OUTPUT RULES:
      - Return all fields defined in JobDescriptionData.
      - Use an empty list for missing responsibilities.
      - Use an empty list for missing requirements.
      - Use null when the company is not specified.
      - Return structured data matching the schema.

      EXPLICITLY IDENTIFIED QUALIFICATIONS:
        {bullet_context}

        These qualifications were extracted directly from the JD.
        Every item above MUST appear in the requirements output.
        Preserve its required/preferred importance.

        If an item describes multiple distinct qualifications,
        preserve each qualification without inventing new ones.

        Do not omit these qualifications even if they are unrelated
        to the job title.

    
      ALLOWED REQUIREMENT CATEGORIES:

      - technical_skill
      - experience
      - education
      - certification
      - language
      - responsibility
      - other

      CATEGORY CLASSIFICATION RULES:

      Use only the categories listed above.

      - technical_skill: Programming languages, frameworks, tools,
        technical knowledge, and technical competencies.
      - experience: Employment history, professional experience,
        project experience, and required years of experience.
      - education: Degrees and academic qualifications.
      - certification: Professional certifications.
      - language: Proficiency in a specific human language,
        such as English, Spanish, or Mandarin.
      - responsibility: Job duties and responsibilities.
      - other: Communication, teamwork, adaptability,
        collaboration, leadership, cultural fit, and soft skills.

      IMPORTANT:
      "communication" is NOT a valid category.
      Classify communication skills as "other".

      Never generate a category outside the allowed values.
    
      JOB DESCRIPTION:
      {job_description}
      """

    result = jd_llm.invoke(prompt)
    
    return {"jd_requirements": result}
