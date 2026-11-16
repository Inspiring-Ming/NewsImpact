"""Measuring analysis quality - pure functions, no I/O.

Used by `GET /v1/evaluation` against the hand-labelled set in data/eval/, so
every analysis chain (word lists, LLM, mixes) is judged on the same examples
before it is trusted in the product.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

from newsimpact.shared.events import Model


class LabelScore(Model):
    label: str
    precision: float
    recall: float
    f1: float
    support: int


class FieldScore(Model):
    field: str
    accuracy: float
    macro_f1: float
    per_label: tuple[LabelScore, ...]


def score_field(field: str, gold: Sequence[str], predicted: Sequence[str]) -> FieldScore:
    """Accuracy, macro-F1 and per-label precision/recall for one predicted field."""
    if len(gold) != len(predicted) or not gold:
        raise ValueError("gold and predicted must be non-empty and aligned")
    labels = sorted(set(gold) | set(predicted))
    tp: Counter[str] = Counter()
    fp: Counter[str] = Counter()
    fn: Counter[str] = Counter()
    for g, p in zip(gold, predicted, strict=True):
        if g == p:
            tp[g] += 1
        else:
            fp[p] += 1
            fn[g] += 1
    per_label = []
    for label in labels:
        precision = tp[label] / (tp[label] + fp[label]) if tp[label] + fp[label] else 0.0
        recall = tp[label] / (tp[label] + fn[label]) if tp[label] + fn[label] else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_label.append(LabelScore(label=label, precision=round(precision, 3),
                                    recall=round(recall, 3), f1=round(f1, 3),
                                    support=tp[label] + fn[label]))  # fmt: skip
    supported = [s for s in per_label if s.support]
    return FieldScore(
        field=field,
        accuracy=round(sum(tp.values()) / len(gold), 3),
        macro_f1=round(sum(s.f1 for s in supported) / len(supported), 3),
        per_label=tuple(per_label),
    )
