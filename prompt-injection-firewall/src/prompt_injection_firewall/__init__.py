"""Explainable prompt-injection detection for local application boundaries."""

from .scanner import Finding, ScanPolicy, ScanReport, normalize_text, scan_text

__all__ = ["Finding", "ScanPolicy", "ScanReport", "normalize_text", "scan_text"]
