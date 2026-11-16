"""Word-list analysis: transparent, deterministic, free.

The baseline that an LLM analyzer must beat on a labelled evaluation set
(ADR 0005). All words and patterns come from the taxonomy file, so
improving them needs no code change.

SentenceExtractor   one claim per sentence that names a known entity
TaxonomyClassifier  speculation, background vs. news, event type, business aspect
AttributionStep     where the claim comes from (outlet cited, company, filing, anonymous)
LexiconSentiment    sentiment from positive/negative word lists
WordListSignal      any word list -> a 0..1 signal (e.g. "uncertainty")
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence

from newsimpact.semantics.models import (
    OTHER,
    Attribution,
    AttributionKind,
    Claim,
    EntityMention,
    Taxonomy,
)
from newsimpact.sources.models import Article

_SENTENCE = re.compile(r"(?<=[.!?])\s+")
_TOKEN = re.compile(r"[a-z']+")


class SentenceExtractor:
    """Splits an article into sentences and keeps those naming a company we follow.

    Names match regardless of capitals, except `exact_case` names, which are also
    ordinary words ("Apple", "Visa") and match only as written.
    """

    version = "sentence-extractor-v2"

    def __init__(self, known_entities: Iterable[str], exact_case: Iterable[str] = ()) -> None:
        names = {e.lower(): re.IGNORECASE for e in known_entities}
        names |= {e: re.NOFLAG for e in exact_case if e.lower() not in names}
        longest_first = sorted(names.items(), key=lambda f: -len(f[0]))
        self._patterns = [re.compile(rf"\b{re.escape(n)}\b", flags) for n, flags in longest_first]

    def extract(self, article: Article) -> Sequence[Claim]:
        text = article.translated_body or article.body  # English pivot for non-English news
        claims: list[Claim] = []
        for i, sentence in enumerate(s for s in _SENTENCE.split(text) if s.strip()):
            entities = self.entities(sentence)
            if entities:
                claims.append(
                    Claim(
                        claim_id=f"{article.article_id}-{i}",
                        article_id=article.article_id,
                        text=sentence.strip(),
                        entities=entities,
                    )
                )
        return claims

    def entities(self, sentence: str) -> tuple[EntityMention, ...]:
        """Known entities in order of appearance (longest alias wins on overlap)."""
        rest = sentence  # matched names are blanked out, so a shorter alias cannot match again
        found: list[tuple[int, EntityMention]] = []
        for pattern in self._patterns:
            match = pattern.search(rest)
            if match:
                mention = EntityMention(
                    name=sentence[match.start() : match.end()], entity_type="company"
                )
                found.append((match.start(), mention))
                rest = (
                    rest[: match.start()]
                    + " " * (match.end() - match.start())
                    + rest[match.end() :]
                )
        return tuple(m for _, m in sorted(found, key=lambda f: f[0]))


class TaxonomyClassifier:
    def __init__(self, taxonomy: Taxonomy) -> None:
        self._t = taxonomy
        self.version = f"taxonomy-classifier-v1/{taxonomy.version}"

    def apply(self, claim: Claim) -> Claim:
        low = claim.text.lower()
        speculative = self.is_speculative(low)
        background = self.is_background(low)
        return claim.model_copy(
            update={
                "is_speculative": speculative,
                # History ("has issued several recalls") is context, not a new event.
                "event_type": OTHER
                if background
                else self.event_type(low, speculative=speculative),
                "aspect": self.aspect(low),
                "signals": {**claim.signals, "background": 1.0 if background else 0.0},
            }
        )

    def is_background(self, low: str) -> bool:
        return any(m in low for m in self._t.words("background"))

    def is_speculative(self, low: str) -> bool:
        return any(m in low for m in self._t.words("speculative"))

    def event_type(self, low: str, *, speculative: bool) -> str:
        for definition in self._t.event_types:
            if definition.speculative is not None and definition.speculative != speculative:
                continue
            if any(p in low for p in definition.patterns):
                return definition.name
        return OTHER

    def aspect(self, low: str) -> str:
        for aspect, keywords in self._t.aspects.items():
            if any(k in low for k in keywords):
                return aspect
        return OTHER


class AttributionStep:
    """Strongest evidence wins: filing > company statement > cited outlet > anonymous > own."""

    def __init__(self, taxonomy: Taxonomy) -> None:
        self._a = taxonomy.attribution
        self.version = f"attribution-v1/{taxonomy.version}"

    def apply(self, claim: Claim) -> Claim:
        return claim.model_copy(update={"attribution": self.attribute(claim.text)})

    def attribute(self, text: str) -> Attribution:
        low = text.lower()
        cited = tuple(
            outlet for outlet, names in self._a.outlets.items() if any(n in low for n in names)
        )
        has_cue = any(c in low for c in self._a.cues)
        kind: AttributionKind = "own_reporting"
        if any(f in low for f in self._a.filing):
            kind = "filing"
        elif any(c in low for c in self._a.company_statement):
            kind = "company_statement"
        elif cited and has_cue:
            kind = "cites_outlet"
        elif any(a in low for a in self._a.anonymous):
            kind = "anonymous"
        return Attribution(kind=kind, cited_outlets=cited if kind == "cites_outlet" else ())


class LexiconSentiment:
    def __init__(self, taxonomy: Taxonomy) -> None:
        self._pos = frozenset(taxonomy.words("positive"))
        self._neg = frozenset(taxonomy.words("negative"))
        self.version = f"lexicon-sentiment-v1/{taxonomy.version}"

    def apply(self, claim: Claim) -> Claim:
        tokens = _TOKEN.findall(claim.text.lower())
        pos = sum(t in self._pos for t in tokens)
        neg = sum(t in self._neg for t in tokens)
        return claim.model_copy(update={"sentiment": round((pos - neg) / (pos + neg + 1), 4)})


class WordListSignal:
    """signal = min(1, matches / saturation). Adds a new measurement with zero schema change."""

    def __init__(self, taxonomy: Taxonomy, name: str, saturation: int = 3) -> None:
        self._name = name
        self._words = frozenset(taxonomy.words(name))
        self._saturation = saturation
        self.version = f"word-signal-{name}-v1/{taxonomy.version}"

    def apply(self, claim: Claim) -> Claim:
        hits = sum(t in self._words for t in _TOKEN.findall(claim.text.lower()))
        value = round(min(1.0, hits / self._saturation), 4)
        return claim.model_copy(update={"signals": {**claim.signals, self._name: value}})
