from blux_coga.contracts.determinism import stable_json_dumps
from blux_coga.contracts.models import ProblemSpec
from blux_coga.contracts.processor import run_contract
from blux_coga.core.state import SessionState
from blux_coga.profiles import load_profile_by_id


def test_profile_schema_validation():
    cpu_profile = load_profile_by_id("cpu")
    gpu_profile = load_profile_by_id("gpu")

    assert cpu_profile.profile_id == "cpu"
    assert gpu_profile.profile_id == "gpu"


def test_profile_determinism():
    profile = load_profile_by_id("cpu")
    problem_spec = ProblemSpec.from_session_state(
        "I'm not sure how to prioritize.", SessionState()
    )
    artifact_a, verdict_a, _state_a = run_contract(problem_spec, profile=profile)
    artifact_b, verdict_b, _state_b = run_contract(problem_spec, profile=profile)

    assert stable_json_dumps(artifact_a.to_dict()) == stable_json_dumps(
        artifact_b.to_dict()
    )
    assert stable_json_dumps(verdict_a.to_dict()) == stable_json_dumps(
        verdict_b.to_dict()
    )


def test_default_run_header_unchanged():
    problem_spec = ProblemSpec.from_session_state(
        "I want to talk about change.", SessionState()
    )
    artifact, verdict, _state = run_contract(problem_spec)

    artifact_header = artifact.run_header.to_dict()
    verdict_header = verdict.run_header.to_dict()

    assert "profile_id" not in artifact_header
    assert "profile_version" not in artifact_header
    assert "profile_id" not in verdict_header
    assert "profile_version" not in verdict_header


def test_profile_metadata_in_headers():
    profile = load_profile_by_id("cpu")
    problem_spec = ProblemSpec.from_session_state("Let's explore options.", SessionState())
    artifact, verdict, _state = run_contract(problem_spec, profile=profile)

    assert artifact.run_header.profile_id == profile.profile_id
    assert artifact.run_header.profile_version == profile.profile_version
    assert verdict.run_header.profile_id == profile.profile_id
    assert verdict.run_header.profile_version == profile.profile_version
