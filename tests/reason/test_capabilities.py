"""Hand-computed expectations for each capability (independent of the pinned regression ids)."""

from __future__ import annotations

from typing import Any

import pytest

from blux_coga.reason import CogaError, run


def req(**kw: Any) -> dict[str, Any]:
    return {"contract": "coga.request", "version": 1, **kw}


EV = [
    {"id": "E1", "claim": "load test passed", "kind": "measurement"},  # 0.9
    {"id": "E2", "claim": "vendor says so", "kind": "testimony"},  # 0.5
    {"id": "E3", "claim": "prod incident", "kind": "observation"},  # 0.8
    {"id": "E4", "claim": "we assume", "kind": "assumption"},  # 0.3
]


def test_analyze_numbers() -> None:
    a = run(
        "reason.analyze",
        req(
            evidence=EV,
            claims=[
                {"id": "C1", "statement": "x", "supported_by": ["E1", "E2"], "contradicted_by": ["E3"]},
                {"id": "C2", "statement": "y", "supported_by": ["E4"]},
                {"id": "C3", "statement": "z", "depends_on": ["C1", "C2"], "supported_by": ["E1"]},
                {"id": "C4", "statement": "w"},
            ],
        ),
    )
    c = {r["claim_id"]: r for r in a["result"]["claims"]}
    assert (c["C1"]["support"], c["C1"]["against"], c["C1"]["status"]) == (0.95, 0.8, "contested")  # 1-(.1*.5)
    assert c["C1"]["confidence"] == 0.15
    assert (c["C2"]["effective_support"], c["C2"]["status"]) == (0.3, "weak")
    assert (c["C3"]["dependency_factor"], c["C3"]["effective_support"]) == (0.3, 0.27)  # .9 x min(.95, .3)
    assert c["C4"]["status"] == "unsupported"
    assert a["result"]["summary"] == {"contested": 1, "unsupported": 1, "weak": 2}
    codes = {s["code"] for s in a["uncertainty"]["sources"]}
    assert {"no-evidence", "assumption-only", "single-source", "contested"} <= codes
    assert a["evidence_refs"] == ["E1", "E2", "E3", "E4"]


def test_plan_schedule() -> None:
    a = run(
        "reason.plan",
        req(
            max_parallel=1,
            tasks=[
                {"id": "design", "title": "D", "effort": 3},
                {"id": "build", "title": "B", "effort": 5, "depends_on": ["design"]},
                {"id": "docs", "title": "Do", "effort": 2, "depends_on": ["design"]},
                {"id": "test", "title": "T", "effort": 2, "depends_on": ["build"]},
                {"id": "release", "title": "R", "effort": 1, "depends_on": ["test", "docs"]},
            ],
        ),
    )
    r = a["result"]
    assert r["order"] == ["design", "build", "docs", "test", "release"]
    assert r["stages"] == [["design"], ["build", "docs"], ["test"], ["release"]]
    assert r["critical_path"] == {"tasks": ["design", "build", "test", "release"], "length": 11.0}
    slack = {s["task_id"]: s["slack"] for s in r["schedule"]}
    assert slack == {"design": 0.0, "build": 0.0, "docs": 5.0, "test": 0.0, "release": 0.0}
    assert r["parallel"]["makespan"] == 13.0  # one at a time: sum of efforts
    assert a["confidence"]["value"] == 1.0


def test_plan_defaults_and_cycles() -> None:
    a = run("reason.plan", req(tasks=[{"id": "a", "title": "A"}, {"id": "b", "title": "B", "depends_on": ["a"]}]))
    assert a["result"]["makespan"] == 2.0 and a["confidence"]["value"] == 0.0
    assert a["uncertainty"]["sources"][0]["code"] == "default-effort"
    with pytest.raises(CogaError) as exc:
        run("reason.plan", req(tasks=[{"id": "a", "title": "A", "depends_on": ["a"]}]))
    assert exc.value.code == "DEPENDENCY_CYCLE"


def test_compare_numbers() -> None:
    a = run(
        "reason.compare",
        req(
            options=[
                {"id": "train", "title": "T", "values": {"time": 40, "cost": 6}},
                {"id": "drive", "title": "D", "values": {"time": 30, "cost": 18}},
                {"id": "walk", "title": "W", "values": {"time": 90, "cost": 18}},
            ],
            criteria=[{"id": "time", "weight": 1, "direction": "min"}, {"id": "cost", "weight": 2, "direction": "min"}],
        ),
    )
    r = a["result"]
    score = {x["option_id"]: x["score"] for x in r["ranking"]}
    # time: 30..90 -> train (90-40)/60, drive 1, walk 0; cost: 6..18 -> train 1, others 0
    assert score == {"train": round((50 / 60 + 2) / 3, 6), "drive": round(1 / 3, 6), "walk": 0.0}
    assert r["leaders"] == ["train"]
    assert r["dominance"] == [{"option_id": "drive", "dominates": "walk"}, {"option_id": "train", "dominates": "walk"}]
    assert r["pareto_front"] == ["drive", "train"]
    assert r["sensitivity"]["stable"] is True


def test_compare_missing_values_and_ties() -> None:
    a = run(
        "reason.compare",
        req(
            options=[
                {"id": "a", "title": "A", "values": {"x": 1, "y": None}},
                {"id": "b", "title": "B", "values": {"x": 1, "y": 2}},
            ],
            criteria=[{"id": "x", "weight": 1, "direction": "max"}, {"id": "y", "weight": 1, "direction": "max"}],
        ),
    )
    assert a["result"]["leaders"] == ["a", "b"]  # a: only x (1.0); b: x=1, y=1 -> both 1.0
    codes = {s["code"] for s in a["uncertainty"]["sources"]}
    assert {"tie", "missing-values"} <= codes
    assert [f["code"] for f in a["findings"]] == ["criterion-not-discriminating", "criterion-not-discriminating"]


def test_rank_pairwise_copeland() -> None:
    a = run(
        "reason.rank",
        req(
            items=[{"id": i} for i in "abcd"],
            comparisons=[
                {"winner": "a", "loser": "b"},
                {"winner": "a", "loser": "c"},
                {"winner": "b", "loser": "c", "weight": 2},
                {"winner": "d", "loser": "a"},
                {"winner": "c", "loser": "d"},
            ],
        ),
    )
    r = a["result"]
    assert [(x["item_id"], x["copeland"], x["net_weight"]) for x in r["ranking"]] == [
        ("a", 2.0, 1.0),
        ("b", 1.0, 1.0),
        ("d", 1.0, 0.0),
        ("c", 1.0, -2.0),
    ]
    assert r["preference_cycle"] == ["a", "b", "c", "d", "a"]  # first cycle in id order
    assert {s["code"] for s in a["uncertainty"]["sources"]} == {"preference-cycle", "incomplete-comparisons"}


def test_rank_scores_and_ties() -> None:
    a = run("reason.rank", req(items=[{"id": "x", "score": 3}, {"id": "y", "score": 7}, {"id": "z", "score": 3}]))
    assert [(r["item_id"], r["rank"]) for r in a["result"]["ranking"]] == [("y", 1), ("x", 2), ("z", 2)]
    assert a["confidence"]["value"] == round(2 / 3, 6)


def test_decompose() -> None:
    a = run(
        "reason.decompose",
        req(
            goal={
                "statement": "Launch",
                "acceptance": [
                    {"id": "A1", "statement": "s", "covered_by": ["signup"]},
                    {"id": "A2", "statement": "b"},
                ],
            },
            items=[
                {"id": "web", "statement": "w"},
                {"id": "signup", "statement": "s", "parent": "web"},
                {"id": "ui", "statement": "u", "parent": "web"},
                {"id": "ops", "statement": "o", "depends_on": ["web"]},
                {"id": "misc", "statement": "m"},
            ],
        ),
    )
    r = a["result"]
    assert r["roots"] == ["misc", "ops", "web"] and r["leaves"] == ["misc", "ops", "signup", "ui"]
    assert r["max_depth"] == 2 and r["work_packages"] == [["misc"], ["ops", "signup", "ui", "web"]]
    assert r["uncovered_acceptance"] == ["A2"] and r["untraced_items"] == ["misc", "ops", "ui"]
    assert a["confidence"]["value"] == 0.5


def test_risk_numbers() -> None:
    a = run(
        "reason.risk",
        req(
            evidence=[{"id": "E", "claim": "history"}],
            appetite=1.2,
            risks=[
                {
                    "id": "outage",
                    "title": "o",
                    "likelihood": 0.4,
                    "impact": 5,
                    "evidence": ["E"],
                    "mitigations": [{"id": "m", "reduction": 0.5, "applies_to": "impact", "evidence": ["E"]}],
                },
                {
                    "id": "vendor",
                    "title": "v",
                    "likelihood": 0.6,
                    "impact": 3,
                    "mitigations": [{"id": "abs", "reduction": 0.3, "applies_to": "likelihood"}],
                },
            ],
        ),
    )
    r = {x["risk_id"]: x for x in a["result"]["risks"]}
    assert (r["outage"]["inherent"], r["outage"]["residual"], r["outage"]["residual_band"]) == (2.0, 1.0, "medium")
    assert (r["vendor"]["inherent"], r["vendor"]["residual"]) == (1.8, 1.26)  # .6*.7*3
    assert a["result"]["ranking"] == ["vendor", "outage"] and a["result"]["over_appetite"] == ["vendor"]
    assert a["confidence"]["value"] == 0.5
    assert {s["code"] for s in a["uncertainty"]["sources"]} == {"unsupported-likelihood", "unverified-mitigation"}


def test_critique_rules() -> None:
    a = run(
        "reason.critique",
        req(
            evidence=[
                *EV,
                {"id": "E5", "claim": "unused"},
                {
                    "id": "E6",
                    "claim": "d",
                    "kind": "dataset",
                    "source": {"dataset": {"dataset_id": "ds", "version": "1", "record_id": "r1"}},
                },
            ],
            claims=[
                {"id": "C1", "statement": "Fast service", "supported_by": ["E2"], "contradicted_by": ["E3"]},
                {"id": "C2", "statement": "Traffic doubles", "supported_by": ["E4"]},
                {"id": "C3", "statement": "fast   SERVICE!", "depends_on": ["C1"]},
                {"id": "C4", "statement": "from data", "supported_by": ["E6"]},
            ],
        ),
    )
    rules = {(f["rule"], tuple(f["refs"])) for f in a["result"]["findings"]}
    assert ("CR001", ("C3",)) in rules  # unsupported
    assert ("CR002", ("C2", "E4")) in rules  # assumption-only
    assert ("CR004", ("C1", "E3")) in rules  # contradicted by stronger evidence
    assert ("CR006", ("C2", "E4")) in rules  # low reliability
    assert ("CR007", ("E1",)) in rules and ("CR007", ("E5",)) in rules  # unused
    assert ("CR011", ("E6",)) in rules  # dataset record without a hash
    assert ("CR012", ("C1", "C3")) in rules  # same statement
    assert a["result"]["findings"][0]["severity"] == "high"
    assert a["confidence"]["value"] == 1.0


def test_critique_needs_something() -> None:
    with pytest.raises(CogaError):
        run("reason.critique", req(evidence=EV))


def test_dataset_linkage() -> None:
    ds = {"dataset_id": "blux-coga-evals", "version": "2.0.0", "record_id": "perf-42", "sha256": "a" * 64}
    a = run(
        "reason.analyze",
        req(
            evidence=[
                {"id": "E", "claim": "c", "kind": "dataset", "source": {"dataset": ds}},
                {"id": "F", "claim": "u", "source": {"dataset": {**ds, "record_id": "x"}}},
            ],
            claims=[{"id": "C", "statement": "s", "supported_by": ["E"]}],
        ),
    )
    assert a["dataset"] == [{**ds, "evidence_id": "E"}]  # only evidence the result uses


def test_repeating_a_reference_cannot_inflate_support() -> None:
    doc = req(evidence=EV, claims=[{"id": "C", "statement": "s", "supported_by": ["E2", "E2", "E2"]}])
    with pytest.raises(CogaError) as exc:
        run("reason.analyze", doc)
    assert exc.value.code == "INVALID_REQUEST" and "unique" in exc.value.message


def test_non_finite_numbers_rejected_through_the_python_api() -> None:
    for bad in (float("nan"), float("inf")):
        with pytest.raises(CogaError):
            run("reason.risk", req(risks=[{"id": "r", "title": "t", "likelihood": 0.5, "impact": bad}]))


def test_cr004_fires_at_equal_reliability() -> None:
    a = run(
        "reason.critique",
        req(
            evidence=[{"id": "P", "claim": "p", "reliability": 0.6}, {"id": "N", "claim": "n", "reliability": 0.6}],
            claims=[{"id": "C", "statement": "s", "supported_by": ["P"], "contradicted_by": ["N"]}],
        ),
    )
    assert "CR004" in {f["rule"] for f in a["result"]["findings"]}


def test_an_option_with_missing_values_dominates_nothing() -> None:
    a = run(
        "reason.compare",
        req(
            options=[
                {"id": "a", "title": "A", "values": {"x": 9, "y": None}},
                {"id": "b", "title": "B", "values": {"x": 1, "y": 1}},
            ],
            criteria=[{"id": "x", "weight": 1, "direction": "max"}, {"id": "y", "weight": 1, "direction": "max"}],
        ),
    )
    assert a["result"]["dominance"] == [] and a["result"]["pareto_front"] == ["a", "b"]


def test_pairwise_tie_scores_half_each() -> None:
    a = run(
        "reason.rank",
        req(
            items=[{"id": "a"}, {"id": "b"}], comparisons=[{"winner": "a", "loser": "b"}, {"winner": "b", "loser": "a"}]
        ),
    )
    assert [(r["item_id"], r["rank"], r["copeland"]) for r in a["result"]["ranking"]] == [("a", 1, 0.5), ("b", 1, 0.5)]
