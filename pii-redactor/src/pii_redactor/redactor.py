from __future__ import annotations

from dataclasses import asdict, dataclass
import re


@dataclass(frozen=True)
class Finding:
    kind: str
    start: int
    end: int
    replacement: str


_RULES: tuple[tuple[str, re.Pattern[str], str], ...] = (
    ("bearer_token", re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{12,}"), "[REDACTED_BEARER]"),
    ("email", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I), "[REDACTED_EMAIL]"),
    ("ipv4", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "[REDACTED_IP]"),
    ("phone", re.compile(r"(?<!\w)(?:\+?\d[\d ()-]{7,}\d)(?!\w)"), "[REDACTED_PHONE]"),
    ("credit_card", re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)"), "[REDACTED_CARD]"),
    ("api_key", re.compile(r"\b(?:sk|pk|api|token)[-_][A-Za-z0-9_-]{12,}\b", re.I), "[REDACTED_KEY]"),
)


def scan(text: str) -> list[Finding]:
    """Return non-overlapping findings, sorted by source position."""
    candidates: list[Finding] = []
    for kind, pattern, replacement in _RULES:
        for match in pattern.finditer(text):
            candidates.append(Finding(kind, match.start(), match.end(), replacement))
    selected: list[Finding] = []
    for finding in sorted(candidates, key=lambda item: (item.start, -(item.end - item.start), item.kind)):
        if selected and finding.start < selected[-1].end:
            continue
        selected.append(finding)
    return selected


def redact(text: str) -> tuple[str, list[Finding]]:
    findings = scan(text)
    pieces: list[str] = []
    cursor = 0
    for finding in findings:
        pieces.append(text[cursor:finding.start])
        pieces.append(finding.replacement)
        cursor = finding.end
    pieces.append(text[cursor:])
    return "".join(pieces), findings


def findings_as_dicts(findings: list[Finding]) -> list[dict[str, object]]:
    return [asdict(item) for item in findings]
