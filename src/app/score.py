material_terms_relevant_for_score = [
    "missing_title",
    "missing_license",
    "missing_keywords",
    "missing_taxonid",
    "missing_edu_context",
]
collections_terms_relevant_for_score = [
    "missing_title",
    "missing_keywords",
    "missing_edu_context",
]


def calc_scores(stats: dict) -> dict:
    if stats["total"] == 0:
        return {k: 0 for k in stats.keys()}

    return {k: 1 - v / stats["total"] for k, v in stats.items() if k != "total"}


def calc_weighted_score(collection_scores: dict, material_scores: dict) -> int:
    score_sum = sum(
        v
        for k, v in collection_scores.items()
        if k in collections_terms_relevant_for_score
    ) + sum(
        v for k, v in material_scores.items() if k in material_terms_relevant_for_score
    )

    return int((100 * score_sum))
