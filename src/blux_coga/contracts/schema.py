"""Schema validation utilities."""

from __future__ import annotations

from typing import Any, Dict


def validate_schema(schema: Dict[str, Any], data: Any) -> None:
    schema_type = schema.get("type")
    allowed_types = schema_type if isinstance(schema_type, list) else [schema_type]
    if data is None:
        if "null" not in allowed_types:
            raise AssertionError("Unexpected null value.")
        return
    if "enum" in schema:
        if data not in schema["enum"]:
            raise AssertionError("Value not in enum.")
    if "allOf" in schema:
        for clause in schema["allOf"]:
            if "if" in clause and "then" in clause:
                if _matches_if(clause["if"], data):
                    validate_schema(clause["then"], data)
            else:
                validate_schema(clause, data)
    if "object" in allowed_types:
        if not isinstance(data, dict):
            raise AssertionError("Expected object.")
        for key in schema.get("required", []):
            if key not in data:
                raise AssertionError(f"Missing key: {key}")
        properties = schema.get("properties", {})
        for key, value in data.items():
            if key in properties:
                validate_schema(properties[key], value)
            elif schema.get("additionalProperties") is False:
                raise AssertionError(f"Unexpected key: {key}")
            elif isinstance(schema.get("additionalProperties"), dict):
                validate_schema(schema["additionalProperties"], value)
    if "array" in allowed_types:
        if not isinstance(data, list):
            raise AssertionError("Expected array.")
        item_schema = schema.get("items")
        if item_schema:
            for item in data:
                validate_schema(item_schema, item)
    if "string" in allowed_types:
        if data is not None and not isinstance(data, str):
            raise AssertionError("Expected string.")
    if "boolean" in allowed_types:
        if data is not None and not isinstance(data, bool):
            raise AssertionError("Expected boolean.")
    if "integer" in allowed_types:
        if data is not None and (
            not isinstance(data, int) or isinstance(data, bool)
        ):
            raise AssertionError("Expected integer.")
    if "number" in allowed_types:
        if data is not None and (
            not isinstance(data, (int, float)) or isinstance(data, bool)
        ):
            raise AssertionError("Expected number.")


def _matches_if(schema: Dict[str, Any], data: Any) -> bool:
    if schema.get("type") == "object" or "properties" in schema:
        if not isinstance(data, dict):
            return False
        properties = schema.get("properties", {})
        for key, prop_schema in properties.items():
            if key not in data:
                return False
            if "enum" in prop_schema and data[key] not in prop_schema["enum"]:
                return False
        return True
    return False
