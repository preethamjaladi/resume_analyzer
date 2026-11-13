"""Calculate the weighted match score and confirmed mandatory gaps."""

from .schemas import State


def calculate_match_score(state: State):
    requirements = state["jd_requirements"].requirements
    matches = state["requirement_matches"]

    # Fixed scoring rules
    importance_weights = {
        "required": 3,
        "preferred": 1
    }

    status_scores = {
        "met": 1.0,
        "partially_met": 0.5,
        "not_met": 0.0,
        "unknown": 0.0
    }

    # Match each requirement to its judgment
    match_lookup = {
        match.requirement_id: match
        for match in matches
    }

    total_weight = 0
    earned_points = 0
    hard_gaps = []

    for requirement in requirements:
        weight = importance_weights[requirement.importance]
        total_weight += weight

        match = match_lookup.get(requirement.requirement_id)

        if match is None:
            raise ValueError(
                f"Missing comparison for {requirement.requirement_id}"
            )

        earned_points += weight * status_scores[match.status]

        # Identify unmet mandatory requirements
        if (
            requirement.is_hard_requirement
            and match.status == "not_met"
        ):
            hard_gaps.append(requirement.description)

    match_score = (
        round((earned_points / total_weight) * 100, 2)
        if total_weight > 0
        else 0.0
    )

    return {
        "match_score": match_score,
        "hard_gaps": hard_gaps
    }
