"""Checks on text a language model writes for people (event briefs, assistant answers).

We state facts and what to check, never what to do with a stock, and we never show a
number the model could have made up: every number must appear in the data it was given.
"""

from __future__ import annotations

import re

ADVICE = re.compile(r"\b(buy|sell|hold|recommend\w*|should|must|price target|undervalued|"
                    r"overvalued|opportunit\w*)\b", re.IGNORECASE)  # fmt: skip
NUMBER = re.compile(r"\d+(?:[.,]\d+)?")


def grounded(text: str, source: str) -> bool:
    """No advice words in `text`, and every number in it also appears in `source`."""
    known = set(NUMBER.findall(source))
    return not ADVICE.search(text) and all(n in known for n in NUMBER.findall(text))
