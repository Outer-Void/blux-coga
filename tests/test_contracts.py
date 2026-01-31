from pathlib import Path

import json

from blux_coga.contracts.determinism import stable_json_dumps
from blux_coga.contracts.models import ProblemSpec
from blux_coga.contracts.processor import run_contract
from blux_coga.contracts.schema import validate_schema
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
