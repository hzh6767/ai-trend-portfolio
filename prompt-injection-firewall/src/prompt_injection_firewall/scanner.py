"""Deterministic prompt-injection scanner.

The scanner intentionally reports signals instead of claiming to understand
intent. It can be placed before a model call or in a review/CI pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata
from typing import Iterable, Pattern


_SEVERITY_WEIGHT = {"low": 10, "medium": 25, "high": 45}


@dataclass(frozen=True)
class Rule:
    rule_id: str
    category: str
    severity: str
    pattern: Pattern[str]
    explanation: str
    remediation: str

    def __post_init__(self) -> None:
        if self.severity not in _SEVERITY_WEIGHT:
            raise ValueError(f"unsupported severity: {self.severity}")


@dataclass(frozen=True)
class Finding:
    rule_id: str
    category: str
    severity: str
    matched_text: str
    start: int
    end: int
    explanation: str
    remediation: str

    def as_dict(self) -> dict[str, object]:
        return {
            "rule_id": self.rule_id,
            "category": self.category,
            "severity": self.severity,
            "matched_text": self.matched_text,
            "start": self.start,
            "end": self.end,
            "explanation": self.explanation,
            "remediation": self.remediation,
        }


@dataclass(frozen=True)
class ScanPolicy:
    """Thresholds for deciding whether findings block a prompt."""

    block_score: int = 45
    block_high: bool = True

    def __post_init__(self) -> None:
        if self.block_score < 1:
            raise ValueError("block_score must be positive")


@dataclass(frozen=True)
class ScanReport:
    normalized_text: str
    findings: tuple[Finding, ...]
    risk_score: int
    blocked: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "normalized_text": self.normalized_text,
            "findings": [finding.as_dict() for finding in self.findings],
            "risk_score": self.risk_score,
            "blocked": self.blocked,
        }


def normalize_text(text: str) -> str:
    """Apply stable Unicode normalization and remove invisible controls."""

    normalized = unicodedata.normalize("NFKC", text or "")
    return "".join(char for char in normalized if unicodedata.category(char) != "Cf" and char not in "\x00\x1b")


def _rule(
    rule_id: str,
    category: str,
    severity: str,
    expression: str,
    explanation: str,
    remediation: str,
) -> Rule:
    return Rule(rule_id, category, severity, re.compile(expression, re.IGNORECASE), explanation, remediation)


DEFAULT_RULES: tuple[Rule, ...] = (
    _rule(
        "PI-001",
        "instruction_override",
        "high",
        r"\b(ignore|disregard|forget|override)\b.{0,50}\b(previous|prior|system|developer|above)\b.{0,35}\b(instruction|message|rule|prompt)s?\b",
        "The text attempts to replace or suppress higher-priority instructions.",
        "Treat the content as untrusted data and preserve the application's instruction hierarchy.",
    ),
    _rule(
        "PI-002",
        "prompt_extraction",
        "high",
        r"\b(reveal|show|print|dump|disclose|repeat)\b.{0,35}\b(system|developer|hidden|original)\b.{0,25}\b(prompt|instructions?|message)\b",
        "The text requests hidden control instructions or system prompt content.",
        "Do not expose hidden prompts; answer only from explicitly authorized context.",
    ),
    _rule(
        "PI-003",
        "jailbreak_persona",
        "high",
        r"\b(DAN|do anything now|no restrictions?|unfiltered mode|developer mode)\b",
        "The text invokes a known jailbreak persona or unrestricted mode.",
        "Ignore persona changes and enforce the configured model and tool policy.",
    ),
    _rule(
        "PI-004",
        "delimiter_spoofing",
        "medium",
        r"(?:</?\s*(system|developer|assistant)\s*>|\[\s*(system|developer|assistant)\s*\]|###\s*(system|developer|assistant))",
        "The text imitates a privileged message delimiter.",
        "Keep message boundaries in the host application instead of trusting user-supplied delimiters.",
    ),
    _rule(
        "PI-005",
        "tool_execution",
        "high",
        r"\b(run|execute|invoke|call)\b.{0,35}\b(shell|command|terminal|powershell|bash|python|tool|function)\b",
        "The text asks for privileged tool or code execution.",
        "Require an explicit allowlist, argument validation, and user approval for tools.",
    ),
    _rule(
        "PI-006",
        "secret_exfiltration",
        "high",
        r"\b(send|post|upload|exfiltrate|output|print|share)\b.{0,40}\b(api\s*key|password|secret|token|credential|private\s*key)\b",
        "The text requests disclosure or transmission of credentials or secrets.",
        "Redact secrets and refuse external transmission unless a narrow policy explicitly permits it.",
    ),
    _rule(
        "PI-007",
        "policy_bypass",
        "medium",
        r"\b(bypass|circumvent|evade|disable)\b.{0,35}\b(safety|policy|filter|guardrail|moderation)\b",
        "The text asks to evade a safety or policy control.",
        "Keep policy enforcement outside the model and reject bypass instructions.",
    ),
)


def scan_text(text: str, policy: ScanPolicy | None = None, rules: Iterable[Rule] = DEFAULT_RULES) -> ScanReport:
    """Scan text and return findings in stable rule/span order."""

    active_policy = policy or ScanPolicy()
    normalized = normalize_text(text)
    findings: list[Finding] = []
    seen: set[tuple[str, int, int]] = set()
    for rule in rules:
        for match in rule.pattern.finditer(normalized):
            key = (rule.rule_id, match.start(), match.end())
            if key in seen:
                continue
            seen.add(key)
            findings.append(
                Finding(
                    rule.rule_id,
                    rule.category,
                    rule.severity,
                    match.group(0),
                    match.start(),
                    match.end(),
                    rule.explanation,
                    rule.remediation,
                )
            )
    findings.sort(key=lambda item: (item.start, item.end, item.rule_id))
    raw_score = sum(_SEVERITY_WEIGHT[finding.severity] for finding in findings)
    score = min(100, raw_score)
    blocked = score >= active_policy.block_score or (
        active_policy.block_high and any(finding.severity == "high" for finding in findings)
    )
    return ScanReport(normalized, tuple(findings), score, blocked)

