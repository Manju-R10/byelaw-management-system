"""Configurable clause-numbering rules for the Extraction Engine (FR-04).

Per the Maintainability NFR, the numbering/heading patterns are kept in this
dedicated, data-driven module rather than hard-coded inside the parser, so new
bye-law formats can be accommodated by editing the ``DEFAULT_RULES`` list alone.

The default ruleset deliberately covers more than the FRS Appendix A examples,
because the real Kerala (ULCCS) bye-law is Malayalam-script and uses:
  * bare Arabic-numeral top-level clauses  -> ``2 പ്രവർത്തനപരിധി``
  * Malayalam / Latin letter sub-clauses   -> ``എ.`` ``ബി.`` / ``A.`` ``B.``
  * parenthesized nested markers           -> ``(എ)`` ``a)`` ``b)``
alongside the classic ``1.`` / ``1.1`` / ``1.1.2`` / ``CHAPTER III`` / ``Rule 12(3)``
patterns from the FRS Appendix.
"""
import re
from dataclasses import dataclass, field
from typing import Callable, List, Optional

# Malayalam Unicode block.
_ML = r"ഀ-ൿ"

# Clause levels.
LEVEL_CHAPTER = 1
LEVEL_CLAUSE = 2
LEVEL_SUBCLAUSE = 3
LEVEL_NESTED = 4


@dataclass
class ClassifiedHeading:
    """Result of classifying a single line/paragraph as a heading."""

    level: int
    number: str
    title: str
    scheme: str


@dataclass
class NumberingRule:
    """A single numbering pattern and how to interpret a match.

    ``level``       : fixed clause level, OR
    ``level_fn``    : callable(match) -> int to derive the level (e.g. dotted numeric).
    ``number_group``: regex group holding the number/marker token.
    ``title_group`` : regex group holding the trailing heading text (0 if none).
    """

    name: str
    pattern: re.Pattern
    scheme: str
    level: Optional[int] = None
    level_fn: Optional[Callable[[re.Match], int]] = None
    number_group: int = 1
    title_group: int = 2

    def classify(self, text: str) -> Optional[ClassifiedHeading]:
        match = self.pattern.match(text)
        if not match:
            return None
        level = self.level if self.level is not None else self.level_fn(match)  # type: ignore[misc]
        number = (match.group(self.number_group) or "").strip()
        title = ""
        if self.title_group and self.title_group <= (match.re.groups):
            title = (match.group(self.title_group) or "").strip()
        return ClassifiedHeading(level=level, number=number, title=title, scheme=self.scheme)


def _dotted_level(match: re.Match) -> int:
    """Level for dotted numeric: 1.1 -> 2, 1.1.2 -> 3 (capped at LEVEL_NESTED)."""
    parts = match.group(1).split(".")
    return min(len(parts), LEVEL_NESTED)


# Order matters: the first matching rule wins, most specific first.
DEFAULT_RULES: List[NumberingRule] = [
    # CHAPTER III  /  CHAPTER 3
    NumberingRule(
        name="chapter_roman",
        pattern=re.compile(r"^\s*(CHAPTER\s+(?:[IVXLCDM]+|\d+))\b[\.\):-]?\s*(.*)$", re.IGNORECASE),
        scheme="roman_chapter",
        level=LEVEL_CHAPTER,
    ),
    # Dotted numeric with >=2 components: 1.1, 5.1.2  (level derived from depth)
    NumberingRule(
        name="dotted_numeric",
        pattern=re.compile(r"^\s*(\d+(?:\.\d+)+)\.?\s+(\D.*)?$"),
        scheme="dotted_numeric",
        level_fn=_dotted_level,
    ),
    # Rule 12(3)  -> sub-clause (alternate style)
    NumberingRule(
        name="rule_paren",
        pattern=re.compile(r"^\s*(Rule\s+\d+\(\d+\))\s*(.*)$", re.IGNORECASE),
        scheme="rule_paren",
        level=LEVEL_SUBCLAUSE,
    ),
    # Bye-law No. 12 -> clause (alternate style)
    NumberingRule(
        name="byelaw_no",
        pattern=re.compile(r"^\s*(Bye-?law\s+No\.?\s*\d+)\s*(.*)$", re.IGNORECASE),
        scheme="byelaw_no",
        level=LEVEL_CLAUSE,
    ),
    # Single numeric with a dot: "1. Name of the Society" -> top-level clause/chapter
    NumberingRule(
        name="single_numeric_dot",
        pattern=re.compile(r"^\s*(\d{1,3})\.\s+(\D.*)$"),
        scheme="numeric",
        level=LEVEL_CHAPTER,
    ),
    # Bare single numeric heading: "2 പ്രവർത്തനപരിധി" (1-3 digits, title starts non-digit)
    NumberingRule(
        name="single_numeric_bare",
        pattern=re.compile(rf"^\s*(\d{{1,3}})\s+([^\d\s][{_ML}A-Za-z].*)$"),
        scheme="numeric",
        level=LEVEL_CHAPTER,
    ),
    # Parenthesized Malayalam/Latin letter: "(എ)" "(a)" -> nested
    NumberingRule(
        name="paren_letter",
        pattern=re.compile(rf"^\s*\(([A-Za-z]|[{_ML}]{{1,3}})\)\s*(.*)$"),
        scheme="paren_letter",
        level=LEVEL_NESTED,
    ),
    # Trailing-paren letter: "a)" "എ)" -> nested
    NumberingRule(
        name="letter_paren",
        pattern=re.compile(rf"^\s*([a-zA-Z]|[{_ML}]{{1,3}})\)\s+(.*)$"),
        scheme="letter_paren",
        level=LEVEL_NESTED,
    ),
    # Letter with dot: "A." "എ." "ബി." -> sub-clause
    NumberingRule(
        name="letter_dot",
        pattern=re.compile(rf"^\s*([A-Za-z]|[{_ML}]{{1,4}})\.\s+(.*)$"),
        scheme="letter_dot",
        level=LEVEL_SUBCLAUSE,
    ),
    # Letter with dot but no trailing text on the line: "എ." (marker alone)
    NumberingRule(
        name="letter_dot_alone",
        pattern=re.compile(rf"^\s*([A-Za-z]|[{_ML}]{{1,4}})\.\s*$"),
        scheme="letter_dot",
        level=LEVEL_SUBCLAUSE,
        title_group=0,
    ),
]


class RuleSet:
    """A configurable ordered collection of numbering rules."""

    def __init__(self, rules: Optional[List[NumberingRule]] = None) -> None:
        self.rules: List[NumberingRule] = rules if rules is not None else list(DEFAULT_RULES)

    def classify(self, text: str) -> Optional[ClassifiedHeading]:
        """Return the heading classification for a line, or None if it is body text."""
        if not text or not text.strip():
            return None
        for rule in self.rules:
            result = rule.classify(text)
            if result is not None:
                return result
        return None


def get_default_ruleset() -> RuleSet:
    return RuleSet()
