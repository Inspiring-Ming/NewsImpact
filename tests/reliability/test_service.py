from newsimpact.reliability.adapters.memory import InMemoryEvidenceStore, InMemoryTrackedSources
from newsimpact.reliability.service import ReliabilityService
from newsimpact.shared.bus import InMemoryEventBus
from newsimpact.sources.models import Source, SourceType


def test_corroboration_record_moves_the_score_and_is_replaced_not_added() -> None:
    sources = InMemoryTrackedSources()
    sources.upsert(
        Source(source_id="n", name="N", source_type=SourceType.MAJOR_OUTLET, domains=("n.test",))
    )
    svc = ReliabilityService(InMemoryEventBus(), sources, InMemoryEvidenceStore())
    assert svc.score_source("n").score == 0.75  # starting estimate for a newspaper
    svc.set_corroboration("n", confirmed=10, unconfirmed=0)
    svc.set_corroboration(
        "n", confirmed=10, unconfirmed=0
    )  # recomputed each round: no double count
    up = svc.score_source("n")
    assert up.score == (7.5 + 10) / 20 and up.supported == 10 and up.prior == 0.75
    svc.set_corroboration("n", confirmed=0, unconfirmed=5)
    assert svc.score_source("n").score < 0.75
