"""Quality gate: the analysis chain must not get worse on the labelled set.

Thresholds are the word-list baseline measured on the labelled set, rounded
down. Raise them when a better chain (e.g. an LLM preset) is adopted; never
lower them to make a code change pass. They are re-measured only when the
labelled set itself changes (2026-11-15: 56 sentences after adding cyber and
job-cut examples; "Helix Cloud said hackers..." is a company statement that
word lists cannot recognise, so attribution moved from 0.96 to 0.946).
"""

from newsimpact.app.config import Settings
from newsimpact.app.views.system import evaluation
from newsimpact.app.wiring import build_services

MINIMUM_ACCURACY = {
    "event_type": 0.65,
    "attribution_kind": 0.94,
    "is_speculative": 0.95,
    "is_background": 0.95,
}


def test_baseline_meets_the_quality_gate() -> None:
    svc = build_services(Settings(env="test", profile="demo"))
    scores = {f.field: f.accuracy for f in evaluation(svc).fields}
    for field, minimum in MINIMUM_ACCURACY.items():
        assert scores[field] >= minimum, (field, scores[field])
