"""Schemas, replay, the eval suite, the CLI, the BLUX adapter and the boundaries of CogA 2."""

from __future__ import annotations

import ast
import io
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from blux_coga.reason import ALGORITHMS, CogaError, blux_adapter, replay, run
from blux_coga.reason.cli import main
from blux_coga.reason.common import schema, validate
from blux_coga.reason.evaluate import run_suite

ROOT = Path(__file__).resolve().parents[2]
EVALS = ROOT / "src" / "blux_coga" / "reason" / "evals"
jsonschema = pytest.importorskip("jsonschema")


def cases() -> list[tuple[str, dict[str, Any] | str, dict[str, Any]]]:
    suite = json.loads((EVALS / "suite.json").read_text())
    return [(c["capability"], (EVALS / c["request"]).read_text(), c["expect"]) for c in suite["cases"]]


def test_bundled_suite_passes() -> None:
    report = run_suite(EVALS)
    assert report["verdict"] == "pass", [c for c in report["cases"] if not c["passed"]]
    kinds = {c["kind"] for c in report["cases"]}
    assert kinds == {"regression", "adversarial"} and report["passed"] >= 24
    assert {c["capability"] for c in report["cases"] if c["kind"] == "regression"} == set(ALGORITHMS)


def test_generated_files_are_current() -> None:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "gen_schemas.py"), "--check"], capture_output=True, text=True
    )
    assert proc.returncode == 0, proc.stderr


@pytest.mark.parametrize("cap", sorted(ALGORITHMS))
def test_schemas_are_valid_draft_2020_12(cap: str) -> None:
    for kind in ("request", "artifact"):
        jsonschema.Draft202012Validator.check_schema(schema(f"{cap}.{kind}.v1.json"))


def test_own_validator_agrees_with_jsonschema() -> None:
    """CogA validates with its own subset validator; the reference implementation must agree on every case."""
    for cap, text, _expect in cases():
        if "NaN" in text or "Infinity" in text:
            continue  # not JSON: CogA rejects these while parsing, before any schema is consulted
        doc = json.loads(text)
        sch = schema(f"{cap}.request.v1.json")
        ours = not validate(doc, sch, sch)
        theirs = jsonschema.Draft202012Validator(sch).is_valid(doc)
        assert ours == theirs, (cap, text[:80])


def test_every_artifact_matches_its_schema_in_jsonschema_too() -> None:
    for cap, text, expect in cases():
        if "error" in expect:
            continue
        artifact = run(cap, json.loads(text), linkage={"operation_id": "op_x", "system": "blux"})
        jsonschema.validate(artifact, schema(f"{cap}.artifact.v1.json"))
        jsonschema.validate(artifact, schema("artifact.v1.json"))


def test_replay() -> None:
    cap, text, _ = cases()[0]
    req = json.loads(text)
    art = run(cap, req, linkage={"operation_id": "op_1", "system": "blux"})
    good = replay(art, req)
    assert good["ok"] and good["artifact"] == art
    tampered = json.loads(json.dumps(art))
    tampered["result"]["claims"][0]["status"] = "supported"
    bad = replay(tampered, req)
    assert not bad["ok"] and bad["checks"]["artifact_id_match"] and not bad["checks"]["document_match"]
    other = json.loads(text)
    other["claims"][0]["supported_by"] = []
    assert not replay(art, other)["checks"]["input_match"]
    with pytest.raises(CogaError):
        replay({"contract": "nope"}, req)


def test_artifact_id_ignores_linkage_only() -> None:
    cap, text, _ = cases()[1]
    a = run(cap, json.loads(text))
    b = run(cap, json.loads(text), linkage={"operation_id": "op_z"})
    assert a["artifact_id"] == b["artifact_id"] and a != b


def test_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    req = tmp_path / "r.json"
    req.write_text((EVALS / "cases" / "risk-basic.json").read_text())
    assert main(["risk", str(req), "-o", str(tmp_path / "a.json")]) == 0
    assert main(["replay", str(tmp_path / "a.json"), "--request", str(req), "-o", str(tmp_path / "re.json")]) == 0
    assert json.loads((tmp_path / "re.json").read_text()) == json.loads((tmp_path / "a.json").read_text())
    capsys.readouterr()
    bad = tmp_path / "bad.json"
    bad.write_text('{"contract": "coga.request", "version": 1}')
    assert main(["risk", str(bad)]) == 3
    assert json.loads(capsys.readouterr().out.splitlines()[0])["error"]["code"] == "INVALID_REQUEST"
    assert main(["validate", "risk", str(req)]) == 0
    assert main(["schema", "plan"]) == 0 and main(["capabilities"]) == 0
    assert main(["eval"]) == 0
    assert main([]) == 2 and main(["nope"]) == 2


def _call(cap: str, payload: Any, ctx: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    out = io.StringIO()
    raw = json.dumps({"capability_id": cap, "input": payload, "context": ctx or {"operation_id": "op_a"}}).encode()
    code = blux_adapter.main(cap, io.BytesIO(raw), out)
    (line,) = out.getvalue().splitlines()
    return code, json.loads(line)


def test_blux_adapter() -> None:
    ctx = {"operation_id": "op_1", "parent_operation_id": "op_0", "session_id": "ses_1", "project_id": "blux-coga"}
    for cap, text, expect in cases():
        if text.lstrip().startswith("{") and "NaN" not in text and "Infinity" not in text:
            code, doc = _call(cap, json.loads(text), ctx)
            if "error" in expect:
                assert code == 1 and doc["error"]["code"] == expect["error"], (cap, doc)
            else:
                assert code == 0 and doc["linkage"] == {**ctx, "capability_id": cap, "system": "blux"}
    code, doc = _call("reason.nope", {})
    assert code == 1 and doc["error"]["code"] == "UNKNOWN_CAPABILITY"
    out = io.StringIO()
    assert blux_adapter.main("reason.rank", io.BytesIO(b"[]"), out) == 1


def test_own_dot_blux_is_valid() -> None:
    sdk = pytest.importorskip("blux_sdk.dot_blux")
    project = sdk.load(ROOT)
    caps = {c.capability_id: c for c in project.capabilities()}
    assert sorted(caps) == sorted(ALGORITHMS)
    for cid, c in caps.items():
        assert c.side_effects == "none" and c.input_schema == schema(f"{cid}.request.v1.json")
        assert c.output_schema == schema(f"{cid}.artifact.v1.json")


SOURCES = sorted((ROOT / "src" / "blux_coga" / "reason").rglob("*.py"))


def test_no_execution_network_or_model_access() -> None:
    banned = {
        "subprocess",
        "socket",
        "urllib",
        "http",
        "requests",
        "httpx",
        "multiprocessing",
        "ctypes",
        "random",
        "time",
        "datetime",
    }
    for path in SOURCES:
        tree = ast.parse(path.read_text())
        names = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        names |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
        assert not names & banned, (path.name, names & banned)


def test_artifacts_hold_no_hidden_reasoning() -> None:
    """CogA artifacts are explicit structures. No field may look like a place for model thoughts."""
    forbidden = ("thought", "chain", "scratchpad", "hidden", "internal", "monologue", "reasoning_trace")
    for cap, text, expect in cases():
        if "error" in expect:
            continue
        keys = _keys(run(cap, json.loads(text)))
        assert not [k for k in keys if any(f in k for f in forbidden)], cap


def _keys(v: Any) -> set[str]:
    if isinstance(v, dict):
        return {k.lower() for k in v} | {k for x in v.values() for k in _keys(x)}
    if isinstance(v, list):
        return {k for x in v for k in _keys(x)}
    return set()
