"""reason.compare/1: weighted multi-criteria comparison.

Each criterion is min-max normalized over the options that have a value (direction "min" is inverted); a
criterion where every value is equal normalizes to 1 and is reported as non-discriminating. An option's
score is the weighted mean over the criteria it has values for; `coverage` is the share of total weight
those criteria carry. Option A dominates B when A is at least as good on every criterion both have, better
on one, and both have values for all criteria. Sensitivity: each weight is halved and increased by half in
turn; the comparison is stable if the leader never changes. Confidence = min(1, lead margin / 0.25) x the
leader's coverage.
"""

from __future__ import annotations

from typing import Any

from blux_coga.reason.common import CogaError, Draft, Evidence, require_refs, unique_ids

EPS = 1e-12


def check(
    request: dict[str, Any], ev: dict[str, Evidence]
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    options = unique_ids(request.get("options", []), "Option")
    criteria = unique_ids(request.get("criteria", []), "Criterion")
    for oid, o in options.items():
        unknown = sorted(set(o.get("values", {})) - set(criteria))
        if unknown:
            raise CogaError(
                "UNKNOWN_REFERENCE",
                f"Option {oid} has values for unknown criteria {unknown}.",
                details={"missing": unknown},
            )
        for cid, refs in sorted(o.get("evidence", {}).items()):
            if cid not in criteria:
                raise CogaError("UNKNOWN_REFERENCE", f"Option {oid} cites evidence for unknown criterion {cid!r}.")
            require_refs(refs, ev, "evidence", f"option {oid}")
    return options, criteria


def scores(
    options: dict[str, dict[str, Any]], criteria: dict[str, dict[str, Any]], weights: dict[str, float]
) -> dict[str, Any]:
    norm: dict[str, dict[str, float]] = {oid: {} for oid in options}
    flat: list[str] = []
    for cid in sorted(criteria):
        vals = {oid: o["values"][cid] for oid, o in options.items() if o.get("values", {}).get(cid) is not None}
        if not vals:
            continue
        lo, hi = min(vals.values()), max(vals.values())
        for oid, v in vals.items():
            n = 1.0 if hi - lo <= EPS else (v - lo) / (hi - lo)
            norm[oid][cid] = n if criteria[cid]["direction"] == "max" else (1.0 if hi - lo <= EPS else 1.0 - n)
        if hi - lo <= EPS and len(options) > 1:
            flat.append(cid)
    total_w = sum(weights[c] for c in sorted(criteria))
    out: dict[str, Any] = {"normalized": norm, "flat": flat, "score": {}, "coverage": {}}
    for oid in sorted(options):
        present = sorted(norm[oid])
        w = sum(weights[c] for c in present)
        out["score"][oid] = sum(weights[c] * norm[oid][c] for c in present) / w if w > 0 else 0.0
        out["coverage"][oid] = w / total_w
    return out


def ranking(score: dict[str, float]) -> list[dict[str, Any]]:
    ordered = sorted(score, key=lambda o: (-score[o], o))
    rows: list[dict[str, Any]] = []
    rank = 0
    last: float | None = None
    for oid in ordered:
        if last is None or abs(score[oid] - last) > 1e-9:
            rank += 1
            last = score[oid]
        rows.append({"option_id": oid, "rank": rank, "score": score[oid]})
    return rows


def leader(score: dict[str, float]) -> list[str]:
    best = max(score.values())
    return sorted(o for o in score if abs(score[o] - best) <= 1e-9)


def dominates(a: dict[str, Any], b: dict[str, Any], criteria: dict[str, dict[str, Any]]) -> bool:
    better = False
    for cid in sorted(criteria):
        va, vb = a.get("values", {}).get(cid), b.get("values", {}).get(cid)
        if va is None or vb is None:
            return False
        sign = 1 if criteria[cid]["direction"] == "max" else -1
        if sign * (va - vb) < 0:
            return False
        if sign * (va - vb) > 0:
            better = True
    return better


def run(request: dict[str, Any], ev: dict[str, Evidence]) -> Draft:
    options, criteria = check(request, ev)
    weights = {cid: float(c["weight"]) for cid, c in criteria.items()}
    s = scores(options, criteria, weights)
    rows = ranking(s["score"])
    for r in rows:
        r["coverage"] = s["coverage"][r["option_id"]]
    dom = [
        {"option_id": a, "dominates": b}
        for a in sorted(options)
        for b in sorted(options)
        if a != b and dominates(options[a], options[b], criteria)
    ]
    dominated = {d["dominates"] for d in dom}
    top = leader(s["score"])
    flips: list[dict[str, Any]] = []
    for cid in sorted(criteria):
        for factor in (0.5, 1.5):
            w = dict(weights)
            w[cid] *= factor
            alt = leader(scores(options, criteria, w)["score"])
            if alt != top:
                flips.append({"criterion": cid, "weight_factor": factor, "leaders": alt})
    ordered = [r["score"] for r in rows]
    margin = ordered[0] - ordered[1] if len(ordered) > 1 else 1.0
    result = {
        "criteria": [{"id": c, "weight": weights[c], "direction": criteria[c]["direction"]} for c in sorted(criteria)],
        "matrix": [
            {
                "option_id": oid,
                "values": {c: options[oid].get("values", {}).get(c) for c in sorted(criteria)},
                "normalized": {c: s["normalized"][oid].get(c) for c in sorted(criteria)},
            }
            for oid in sorted(options)
        ],
        "ranking": rows,
        "leaders": top,
        "pareto_front": sorted(set(options) - dominated),
        "dominance": dom,
        "sensitivity": {"stable": not flips, "flips": flips},
        "margin": margin,
    }
    refs = {e for o in options.values() for es in o.get("evidence", {}).values() for e in es}
    draft = Draft(
        result=result,
        confidence=min(1.0, margin / 0.25) * s["coverage"][top[0]],
        confidence_basis="min(1, score margin between the first two ranks / 0.25) x leader's criterion coverage",
        evidence_refs=refs,
    )
    if len(top) > 1:
        draft.gap("tie", f"{len(top)} options tie for the lead.", top)
    if flips:
        draft.gap(
            "weight-sensitive",
            "The leader changes when a single weight moves by 50%.",
            sorted({f["criterion"] for f in flips}),
        )
    missing = sorted(oid for oid in options if s["coverage"][oid] < 1.0)
    if missing:
        draft.gap("missing-values", f"{len(missing)} option(s) lack values for some criteria.", missing)
    for cid in s["flat"]:
        draft.note("criterion-not-discriminating", f"Every option has the same value for {cid}.", [cid])
    if len(options) == 1:
        draft.note("single-option", "Only one option: nothing is being compared.", sorted(options), "medium")
    return draft
