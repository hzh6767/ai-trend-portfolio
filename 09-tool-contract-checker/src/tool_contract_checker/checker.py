"""Validate agent tool contracts and invocations without executing tools."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping

_TYPES = {"string", "integer", "number", "boolean", "array", "object"}
_SHELL_RE = re.compile(r"(?:&&|\|\||[;&|`]|\\x00|\$\(|\n)")


@dataclass(frozen=True)
class ToolContract:
    name: str
    description: str
    parameters: dict[str, dict[str, Any]]
    required: tuple[str, ...] = ()
    allow_extra: bool = False

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ToolContract":
        return cls(
            name=str(data.get("name", "")),
            description=str(data.get("description", "")),
            parameters=dict(data.get("parameters", {})),
            required=tuple(data.get("required", ())),
            allow_extra=bool(data.get("allow_extra", False)),
        )


@dataclass(frozen=True)
class CheckResult:
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {"valid": self.valid, "errors": list(self.errors), "warnings": list(self.warnings)}


def validate_contract(contract: ToolContract) -> tuple[str, ...]:
    errors: list[str] = []
    if not contract.name.strip():
        errors.append("name must not be empty")
    if not isinstance(contract.parameters, dict):
        errors.append("parameters must be an object")
        return tuple(errors)
    if any(not isinstance(name, str) or not name.strip() for name in contract.parameters):
        errors.append("parameter names must be non-empty strings")
    for name, schema in contract.parameters.items():
        if not isinstance(schema, dict):
            errors.append(f"{name}: schema must be an object")
            continue
        kind = schema.get("type")
        if kind not in _TYPES:
            errors.append(f"{name}: unsupported type {kind!r}")
        if "enum" in schema and (not isinstance(schema["enum"], list) or not schema["enum"]):
            errors.append(f"{name}: enum must be a non-empty list")
        if "minimum" in schema and not isinstance(schema["minimum"], (int, float)):
            errors.append(f"{name}: minimum must be numeric")
        if "minLength" in schema and (not isinstance(schema["minLength"], int) or schema["minLength"] < 0):
            errors.append(f"{name}: minLength must be a non-negative integer")
    unknown_required = sorted(set(contract.required) - set(contract.parameters))
    if unknown_required:
        errors.append("required contains unknown parameter(s): " + ", ".join(unknown_required))
    return tuple(errors)


def _type_matches(value: Any, kind: str) -> bool:
    return {"string": isinstance(value, str), "integer": isinstance(value, int) and not isinstance(value, bool), "number": isinstance(value, (int, float)) and not isinstance(value, bool), "boolean": isinstance(value, bool), "array": isinstance(value, list), "object": isinstance(value, dict)}.get(kind, False)


def check_invocation(contract: ToolContract, arguments: Mapping[str, Any]) -> CheckResult:
    errors = list(validate_contract(contract))
    warnings: list[str] = []
    if not isinstance(arguments, Mapping):
        return CheckResult(False, tuple(errors + ["arguments must be an object"]), tuple(warnings))
    missing = sorted(set(contract.required) - set(arguments))
    errors.extend(f"missing required parameter: {name}" for name in missing)
    if not contract.allow_extra:
        errors.extend(f"unknown parameter: {name}" for name in sorted(set(arguments) - set(contract.parameters)))
    for name, value in arguments.items():
        schema = contract.parameters.get(name)
        if schema is None:
            continue
        kind = schema.get("type")
        if not _type_matches(value, kind):
            errors.append(f"{name}: expected {kind}")
            continue
        if "enum" in schema and value not in schema["enum"]:
            errors.append(f"{name}: value is not allowed")
        if isinstance(value, str):
            if len(value) < schema.get("minLength", 0):
                errors.append(f"{name}: string is shorter than minLength")
            if _SHELL_RE.search(value):
                warnings.append(f"{name}: shell metacharacters detected")
            if name.lower().endswith(("path", "file", "filename")) and (".." in value.replace("\\", "/").split("/") or value.startswith(("/", "\\"))):
                warnings.append(f"{name}: path traversal or absolute path detected")
        if isinstance(value, (int, float)) and not isinstance(value, bool) and "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{name}: value is below minimum")
    return CheckResult(not errors, tuple(errors), tuple(warnings))
