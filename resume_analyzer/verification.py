"""Deterministic evidence, skill, degree, and experience verification."""

import re
from datetime import date, datetime

from .schemas import (
    JobRequirement, RequirementMatch, ResumeSections, State, VerificationResult,
)


def route_requirement(requirement: JobRequirement) -> str:

    category_routes = {
        "education": "education",
        "experience": "experience",
        "certification": "explicit_evidence",
        "language": "explicit_evidence",
        "technical_skill": "skill_matching",
        "responsibility": "semantic_review",
        "other": "semantic_review"
    }

    return category_routes[requirement.category]

def verify_evidence(match: RequirementMatch, resume: str):
    if match.evidence is None:
        return match.status in ("not_met", "unknown")

    def normalize(text):
        return re.sub(r"\s+", " ", text).strip()

    evidence = normalize(match.evidence)
    original = normalize(resume)

    # First check: exact continuous quote
    if evidence in original:
        return True

    # Second check: multiple independent evidence lines
    lines = [
        normalize(line).lstrip("- ").strip()
        for line in match.evidence.splitlines()
        if line.strip()
    ]

    if len(lines) > 1:
        return all(line and line in original for line in lines)

    return False


SKILL_ALIASES = {
    "javascript": ["js", "javascript"],
    "python": ["python", "python3"],
    "postgresql": ["postgresql", "postgres", "psql"],
    "rest apis": ["rest api", "restful api", "rest endpoints"],
    "docker": ["docker", "containerization"],
    "react": ["react", "react.js", "reactjs"],
    "git": ["git", "version control using git"],
    "cloud technologies": ["aws", "azure", "google cloud", "gcp"]
}


# Step 2: Detect skills and their aliases
def skill_mentioned(skill: str, resume: str) -> bool:
    skill = skill.lower().strip()
    resume_lower = resume.lower()

    aliases = [skill] + SKILL_ALIASES.get(skill, [])

    for alias in aliases:
        pattern = rf"(?<!\w){re.escape(alias)}(?!\w)"

        if re.search(pattern, resume_lower):
            return True

    return False


# Step 3: Detect potential contradictions
def detect_skill_contradictions(state: State):
    requirements = state["jd_requirements"].requirements

    match_lookup = {
        match.requirement_id: match
        for match in state["requirement_matches"]
    }

    contradictions = []

    for requirement in requirements:
        if requirement.category != "technical_skill":
            continue

        match = match_lookup[requirement.requirement_id]

        found = skill_mentioned(
            requirement.description,
            state["resume"]
        )

        if match.status == "not_met" and found:
            contradictions.append({
                "requirement_id": requirement.requirement_id,
                "issue": "Possible false negative",
                "requirement": requirement.description
            })

        elif match.status == "met" and not found:
            contradictions.append({
                "requirement_id": requirement.requirement_id,
                "issue": "Needs semantic evidence review",
                "requirement": requirement.description
            })

    return contradictions


#Degree Level Validation
DEGREE_LEVELS = {
    "associate": 1,
    "bachelor": 2,
    "master": 3,
    "doctorate": 4,
}

DEGREE_ALIASES = {
    "associate": ["associate", "a.s.", "a.a."],
    "bachelor": ["bachelor", "b.s.", "b.a.", "b.tech", "b.e."],
    "master": ["master", "m.s.", "m.a.", "m.tech", "m.sc", "mba"],
    "doctorate": ["phd", "ph.d.", "doctorate", "doctoral"],
}


def detect_degree_level(text: str):
    text = text.lower()

    for degree, aliases in DEGREE_ALIASES.items():
        for alias in aliases:
            pattern = rf"(?<!\w){re.escape(alias)}(?!\w)"
            if re.search(pattern, text):
                return DEGREE_LEVELS[degree]

    return None


def verify_education(requirement: JobRequirement,
                     resume: ResumeSections):

    required_level = detect_degree_level(
        requirement.description
    )

    if required_level is None:
        return "needs_review"

    education_levels = [
        detect_degree_level(edu.degree)
        for edu in resume.education
    ]

    education_levels = [
        level for level in education_levels
        if level is not None
    ]

    if not education_levels:
        return "insufficient_evidence"

    if max(education_levels) >= required_level:
        return "degree_level_met"

    return "degree_level_not_met"


#YOE Validation


def parse_work_date(value: str):
    if not value:
        return None

    value = value.strip()

    if value.lower() in ["present", "current", "now"]:
        return date.today()

    for fmt in ["%b %Y", "%B %Y", "%Y-%m", "%Y"]:
        try:
            parsed = datetime.strptime(value, fmt)
            return date(parsed.year, parsed.month, 1)
        except ValueError:
            continue

    return None


def calculate_experience_years(resume: ResumeSections):
    periods = []

    for job in resume.experience:
        start = parse_work_date(job.start_date)
        end = parse_work_date(job.end_date)

        if start is None or end is None or end < start:
            continue

        # Work with calendar months
        start_month = start.year * 12 + start.month
        end_month = end.year * 12 + end.month

        periods.append((start_month, end_month))

    if not periods:
        return 0.0

    # Merge overlapping employment periods
    periods.sort()
    merged = []

    for start, end in periods:
        if merged and start <= merged[-1][1] + 1:
            merged[-1] = (
                merged[-1][0],
                max(merged[-1][1], end)
            )
        else:
            merged.append((start, end))

    total_months = sum(
        end - start + 1
        for start, end in merged
    )

    return round(total_months / 12, 2)


def verify_experience(requirement: JobRequirement,
                      resume: ResumeSections):

    description = requirement.description.lower()

    # Extract required years
    match = re.search(
        r"(\d+)\s*\+?\s*(?:years|yrs)",
        description
    )

    if not match:
        return {
            "status": "needs_review",
            "reason": "No numerical experience requirement found"
        }

    required_years = int(match.group(1))
    actual_years = calculate_experience_years(resume)

    if actual_years >= required_years:
        return {
            "status": "duration_met",
            "required_years": required_years,
            "actual_years": actual_years,
            "reason": "Duration satisfied; relevance not yet verified"
        }

    return {
        "status": "duration_not_met",
        "required_years": required_years,
        "actual_years": actual_years,
        "reason": "Documented experience is below the required duration"
    }


def verify_requirements(state: State):
    requirements = state["jd_requirements"].requirements
    matches = state["requirement_matches"]
    resume = state["resume"]
    resume_data = state["resume_sections"]

    match_lookup = {
        match.requirement_id: match
        for match in matches
    }
    results = []
    validated_matches = []

    for req in requirements:
        match = match_lookup[req.requirement_id]
        method = route_requirement(req)

        status = "needs_review"
        explanation = "Requires additional verification"

        # 1. Check original resume evidence
        if not verify_evidence(match, resume):
            status = "contradiction"
            explanation = "Evidence quote missing or invalid"

        # 2. Verify technical skills
        elif method == "skill_matching":

            if match.status in ("met", "partially_met"):
                status = "verified"
                explanation = "Supporting resume evidence verified"

            elif match.status == "not_met":
                status = "verified"
                explanation = "Requirement not demonstrated in resume"

            else:
                status = "needs_review"
                explanation = "Unable to determine skill match"

        # 3. Verify education
        elif method == "education":
            degree_result = verify_education(req, resume_data)

            if degree_result == "degree_level_met":
                field_matched = any(
                    edu.field_of_study.strip()
                    and edu.field_of_study.lower() in req.description.lower()
                    for edu in resume_data.education
                    if detect_degree_level(edu.degree)
                    and detect_degree_level(edu.degree)
                        >= detect_degree_level(req.description)
                )

                if field_matched:
                    status = "verified"
                    explanation = "Required degree level and field documented in resume"
                else:
                    if match.status == "not_met":
                        status = "verified"
                        explanation = "Required field of study not demonstrated"
                    else:
                        status = "needs_review"
                        explanation = "Degree level matches; field needs review"

            elif degree_result == "degree_level_not_met":
                status = "verified"
                explanation = "Required degree level not demonstrated in resume"
                match = match.model_copy(update={"status": "not_met"})

            else:
                status = "needs_review"
                explanation = f"Education check: {degree_result}"

        # 4. Verify experience
        elif method == "experience":
            experience_result = verify_experience(req, resume_data)

            if experience_result["status"] == "duration_not_met":
                dates_valid = all(
                    parse_work_date(job.start_date) is not None
                    and parse_work_date(job.end_date) is not None
                    for job in resume_data.experience
                )

                if dates_valid and resume_data.experience:
                    status = "verified"
                    explanation = (
                        f"Documented experience: {experience_result['actual_years']} "
                        f"years; required: {experience_result['required_years']} years"
                    )
                    match = match.model_copy(update={"status": "not_met"})
                else:
                    status = "needs_review"
                    explanation = "Some employment dates are missing or invalid"

            else:
                if experience_result.get("reason") == "No numerical experience requirement found":
                    status = "verified"
                    explanation = "No numerical duration requirement; retaining original classification"
                else:
                    status = "needs_review"
                    explanation = str(experience_result)

        # 5. Explicit language requirements
        elif req.category == "language":
            # Only check declared language information.
            declared = " ".join(resume_data.languages).lower()
            language_found = any(
                language in declared
                for language in [
                    "mandarin", "english", "spanish",
                    "french", "german", "hindi",
                    "japanese", "korean", "arabic"
                ]
                if language in req.description.lower()
            )

            if match.status == "met" and language_found:
                status = "verified"
                explanation = "Required language explicitly declared"

            elif match.status == "met" and not language_found:
                status = "contradiction"
                explanation = "Required language not declared"

            elif match.status == "not_met" and resume_data.languages and not language_found:
                status = "verified"
                explanation = "Required language not demonstrated in declared languages"

            else:
                status = "needs_review"
                explanation = "Language proficiency needs review"

        # Other categories, including certifications,
        # remain flagged for review.

        results.append(
            VerificationResult(
                requirement_id=req.requirement_id,
                verification_method=method,
                status=status,
                explanation=explanation
            )
        )

        # Do not award points for unresolved positive judgments
        # or treat contradicted missing judgments as confirmed gaps.
        if status != "verified":
            match = match.model_copy(update={"status": "unknown"})

        validated_matches.append(match)

    return {
        "verification_results": results,
        "requirement_matches": validated_matches
    }
