"""Small, explicit JSON output guard with no network or model dependency."""

from __future__ import annotations

import json
import re
from typing import Any


class ValidationError(ValueError):
    """Raised when model output is not safe for the requested schema."""


def extract_json(text: str) -> Any:
    """Parse exactly one JSON document, accepting one fenced code block."""
    raw = text.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*\n?(.*?)\n?```", raw, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        raw = fenced.group(1).strip()
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON: {exc.msg} at character {exc.pos}") from exc
    return value


def validate(value: Any, schema: dict[str, Any], path: str = "$", *, root: bool = True) -> Any:
    """Validate a JSON value against the supported schema subset and return it."""
    if not isinstance(schema, dict):
        raise ValidationError(f"{path}: schema must be an object")
    if "enum" in schema and value not in schema["enum"]:
        raise ValidationError(f"{path}: value is not in enum")
    kind = schema.get("type")
    checks = {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }
    if kind in checks and not checks[kind]:
        raise ValidationError(f"{path}: expected {kind}")
    if isinstance(value, dict):
        required = schema.get("required", [])
        if not isinstance(required, list) or any(not isinstance(k, str) for k in required):
            raise ValidationError(f"{path}: required must be a list of strings")
        missing = [key for key in required if key not in value]
        if missing:
            raise ValidationError(f"{path}: missing required field(s): {', '.join(missing)}")
        properties = schema.get("properties", {})
        if not isinstance(properties, dict):
            raise ValidationError(f"{path}: properties must be an object")
        if schema.get("additionalProperties") is False:
            extras = sorted(set(value) - set(properties))
            if extras:
                raise ValidationError(f"{path}: unexpected field(s): {', '.join(extras)}")
        for key, child_schema in properties.items():
            if key in value:
                validate(value[key], child_schema, f"{path}.{key}", root=False)
    if isinstance(value, list) and "items" in schema:
        for index, item in enumerate(value):
            validate(item, schema["items"], f"{path}[{index}]", root=False)
    if root and kind is None and "properties" not in schema and "items" not in schema and "enum" not in schema:
        raise ValidationError("$: schema has no constraints")
    return value
