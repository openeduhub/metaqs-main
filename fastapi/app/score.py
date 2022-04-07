import math
from enum import Enum


class ScoreModulator(str, Enum):
    LINEAR = "linear"
    SQUARE = "square"
    CUBE = "cube"

    def __call__(self, v: float):
        if self is self.LINEAR:
            return v
        elif self is self.SQUARE:
            return math.sqrt(v)
        elif self is self.CUBE:
            return math.pow(v, 1.0 / 3)
        return v


class ScoreWeights(str, Enum):
    UNIFORM = (
        "uniform",
        {
            "collections": {
                "missing_title": 1,
                "missing_keywords": 1,
                "missing_edu_context": 1,
            },
            "materials": {
                "missing_title": 1,
                "missing_license": 1,
                "missing_keywords": 1,
                "missing_taxonid": 1,
                "missing_edu_context": 1,
            },
        },
    )

    def __new__(cls, value: str, weights: dict):
        obj = str.__new__(cls, [value])
        obj._value_ = value
        obj.weights = weights
        return obj


def calc_scores(stats: dict, score_modulator: ScoreModulator) -> dict:
    if stats["total"] == 0:
        return {k: 0 for k in stats.keys()}

    return {
        k: 1 - score_modulator(v / stats["total"])
        for k, v in stats.items()
        if k != "total"
    }


def calc_weighted_score(
    collection_scores: dict, material_scores: dict, score_weights: ScoreWeights
) -> int:
    score_ = sum(
        score_weights.weights["collections"].get(k, 0) * v
        for k, v in collection_scores.items()
    ) + sum(
        score_weights.weights["materials"].get(k, 0) * v
        for k, v in material_scores.items()
    )

    sum_weights = sum(
        score_weights.weights["collections"].get(k, 0) for k in collection_scores.keys()
    ) + sum(
        score_weights.weights["materials"].get(k, 0) for k in material_scores.keys()
    )

    return int((100 * score_) / sum_weights)
