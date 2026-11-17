"""Pure functions, no I/O: a company's part in a deal, and measuring analysis quality.

deal_role: buyer, target or seller, read from where the company's name stands
relative to deal wording (taxonomy.json word lists "deal_*"). Markets react to
the two sides differently (targets jump, buyers move little), so the expected
share price move depends on it.

Quality: used by `GET /v1/evaluation` against the hand-labelled set in
data/eval/, so every analysis chain (word lists, LLM, mixes) is judged on the
same examples before it is trusted in the product.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Literal

from newsimpact.shared.events import Model

DealRole = Literal["buyer", "target", "seller"]

# Where the company's own clause ends: "X shares rose after Y agreed to buy" is about Y buying.
# Punctuation ends it only before a space ("(NYSE:XOM)" and "28.7%" do not).
_CLAUSE_END = re.compile(r"[.;:!?](\s|$)|\b(after|as|while|when|because|but|amid)\b")
_WINDOW = 80  # characters around the name: about one clause of a headline


def deal_role(text: str, names: Sequence[str], cues: Mapping[str, Sequence[str]]
              ) -> DealRole | None:  # fmt: skip
    """The company's part in the deal a sentence describes, or None when unclear.

    cues (taxonomy.json): deal_seller / deal_buyer / deal_target_after = wording right after
    the name; deal_target_before = wording right before it; deal_asset = a unit, asset or
    project of the company being sold ("to buy QBE's credit unit" -> QBE sells)."""
    low = " ".join(text.lower().split())
    for name in sorted(names, key=len, reverse=True):
        for m in re.finditer(rf"\b{re.escape(name.lower())}\b", low):
            before = low[max(0, m.start() - _WINDOW) : m.start()]
            after = low[m.end() : m.end() + _WINDOW]
            clause = after[: end.start()] if (end := _CLAUSE_END.search(after)) else after
            head = " ".join(after.split()[:5])  # the words right after the name
            bought = _has(before[-40:], cues, "deal_target_before")
            # "to buy Amazon data centers", "Rio Tinto project acquisition": a part is sold
            part_sold = _has(head, cues, "deal_asset") and (
                bought or any(w in head for w in ("acquisition", "sale"))
            )
            if part_sold or _has(clause, cues, "deal_seller"):
                return "seller"
            if before.rstrip().endswith(" by") or _has(clause, cues, "deal_buyer"):
                return "buyer"
            if bought or _has(after, cues, "deal_target_after"):
                return "target"
    return None


def _has(text: str, cues: Mapping[str, Sequence[str]], key: str) -> bool:
    return any(c in text for c in cues.get(key, ()))


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
