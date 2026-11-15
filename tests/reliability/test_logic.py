from newsimpact.reliability.logic import PRIORS, beta_posterior, claim_reliability
from newsimpact.sources.models import SourceType


def test_prior_reflects_source_type() -> None:
    wire, *_ = beta_posterior(PRIORS[SourceType.WIRE], 0, 0)
    blog, *_ = beta_posterior(PRIORS[SourceType.BLOG], 0, 0)
    assert wire > blog


def test_evidence_moves_score_and_narrows_interval() -> None:
    m0, lo0, hi0 = beta_posterior((1, 1), 0, 0)
    m1, lo1, hi1 = beta_posterior((1, 1), 40, 2)
    assert m1 > m0
    assert (hi1 - lo1) < (hi0 - lo0)


def test_retractions_lower_score() -> None:
    good, *_ = beta_posterior((6, 2), 10, 0)
    bad, *_ = beta_posterior((6, 2), 0, 10)
    assert good > 0.8 > 0.5 > bad


def test_corroboration_raises_and_speculation_lowers_claim_reliability() -> None:
    assert claim_reliability(0.6, [0.7, 0.5]) > claim_reliability(0.6)
    assert claim_reliability(0.8, is_speculative=True) < claim_reliability(0.8)


def test_every_source_type_starts_with_the_same_weight_of_evidence() -> None:
    assert {round(a + b, 6) for a, b in PRIORS.values()} == {10.0}
