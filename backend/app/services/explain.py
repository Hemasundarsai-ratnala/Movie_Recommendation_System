from typing import Dict, Any

def generate_explanation(rec: Dict[str, Any], is_cold_start: bool = False) -> str:
    """
    Synthesizes human-readable explanations strictly from computed signal scores.
    Never fabricates reasons.
    """
    if is_cold_start:
        if rec.get("popularity_score", 0) > 0:
            return f"Top-rated community favorite with a Bayesian weighted score of {rec['weighted_rating']} ({rec['rating_count']} ratings)."
        return "Popular selection across the platform."

    c_score = rec.get("content_score", 0.0)
    cb_score = rec.get("collaborative_score", 0.0)
    p_score = rec.get("popularity_score", 0.0)
    seed_title = rec.get("top_contributing_seed_title")

    has_seed = seed_title is not None and len(seed_title) > 0

    if cb_score >= 0.20 and c_score >= 0.20 and has_seed:
        return f"Strong collaborative signal from users who also rated '{seed_title}' highly, combined with a matching genre profile."
    elif cb_score >= 0.20 and has_seed:
        return f"Strong collaborative pattern: users who liked '{seed_title}' frequently enjoyed this film."
    elif c_score >= 0.20 and has_seed:
        return f"Shares matching genres and title keywords with '{seed_title}'."
    elif cb_score >= 0.15:
        return "Recommended based on community collaborative rating patterns."
    elif c_score >= 0.15:
        return f"High content similarity in genres ({rec['genres']})."
    else:
        return f"High overall community popularity (Bayesian WR {rec['weighted_rating']})."
