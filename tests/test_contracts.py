from pathlib import Path

import json

from blux_coga.contracts.determinism import stable_json_dumps
from blux_coga.contracts.models import ProblemSpec
from blux_coga.contracts.processor import run_contract
from blux_coga.core.state import SessionState


def test_deterministic_outputs():
    state = SessionState()
    problem_spec = ProblemSpec.from_session_state(
        "I'm not sure what I want to focus on.", state
    )
    artifact_a, verdict_a, _state_a = run_contract(problem_spec)
    artifact_b, verdict_b, _state_b = run_contract(problem_spec)

    assert stable_json_dumps(artifact_a.to_dict()) == stable_json_dumps(
        artifact_b.to_dict()
    )
    assert stable_json_dumps(verdict_a.to_dict()) == stable_json_dumps(
        verdict_b.to_dict()
    )


def test_schema_validation():
    base_dir = Path(__file__).resolve().parents[1]
    schemas_dir = base_dir / "schemas"

    problem_spec = ProblemSpec.from_session_state(
        "I want to talk about change.", SessionState()
    )
    artifact, verdict, _state = run_contract(problem_spec)

    thought_schema = json.loads(
        (schemas_dir / "thought_artifact.schema.json").read_text(encoding="utf-8")
    )
    verdict_schema = json.loads(
        (schemas_dir / "reasoning_verdict.schema.json").read_text(encoding="utf-8")
    )

    validate_schema(thought_schema, artifact.to_dict())
    validate_schema(verdict_schema, verdict.to_dict())


def validate_schema(schema: dict, data: object) -> None:
    schema_type = schema.get("type")
    allowed_types = schema_type if isinstance(schema_type, list) else [schema_type]
    if data is None:
        assert "null" in allowed_types
        return
    if "enum" in schema:
        assert data in schema["enum"]
    if "allOf" in schema:
        for clause in schema["allOf"]:
            if "if" in clause and "then" in clause:
                if _matches_if(clause["if"], data):
                    validate_schema(clause["then"], data)
            else:
                validate_schema(clause, data)
    if "object" in allowed_types:
        assert isinstance(data, dict)
        for key in schema.get("required", []):
            assert key in data
        properties = schema.get("properties", {})
        for key, value in data.items():
            if key in properties:
                validate_schema(properties[key], value)
            elif schema.get("additionalProperties") is False:
                raise AssertionError(f"Unexpected key: {key}")
            elif isinstance(schema.get("additionalProperties"), dict):
                validate_schema(schema["additionalProperties"], value)
    if "array" in allowed_types:
        assert isinstance(data, list)
        item_schema = schema.get("items")
        if item_schema:
            for item in data:
                validate_schema(item_schema, item)
    if "string" in allowed_types:
        if data is not None:
            assert isinstance(data, str)
    if "boolean" in allowed_types:
        if data is not None:
            assert isinstance(data, bool)


def _matches_if(schema: dict, data: object) -> bool:
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
