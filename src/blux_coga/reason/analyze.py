"""reason.analyze/1: how well is each claim supported?

support(c)  = noisy-OR of the reliabilities of the evidence supporting c
against(c)  = noisy-OR of the reliabilities of the evidence contradicting c
effective   = support x min(effective support of every claim c depends on)   (dependencies are a DAG)
status      = unsupported (no evidence) | supported (eff >= .5, against < .5) | refuted (against >= .5, eff < .5)
              | contested (both >= .5) | weak (otherwise)
confidence  = |effective - against|, the strength of the balance
"""

from __future__ import annotations

from typing import Any

from blux_coga.reason.common import (
    CogaError,
    Draft,
    Evidence,
    find_cycle,
    noisy_or,
    require_refs,
    topo_order,
    unique_ids,
)


def claim_scores(claims: dict[str, dict[str, Any]], ev: dict[str, Evidence]) -> dict[str, dict[str, Any]]:
    deps = {cid: list(c.get("depends_on", [])) for cid, c in claims.items()}
    out: dict[str, dict[str, Any]] = {}
    for cid in topo_order(list(claims), deps):
        c = claims[cid]
        sup = sorted(c.get("supported_by", []))
        con = sorted(c.get("contradicted_by", []))
        support = noisy_or([ev[e].reliability for e in sup])
        against = noisy_or([ev[e].reliability for e in con])
        factor = min((out[d]["effective_support"] for d in sorted(deps[cid])), default=1.0)
        effective = support * factor
        if not sup and not con:
            status = "unsupported"
        elif effective >= 0.5 and against >= 0.5:
            status = "contested"
        elif effective >= 0.5:
            status = "supported"
        elif against >= 0.5:
            status = "refuted"
        else:
            status = "weak"
        out[cid] = {
            "claim_id": cid,
            "status": status,
            "support": support,
            "against": against,
            "dependency_factor": factor,
            "effective_support": effective,
            "confidence": abs(effective - against),
            "supported_by": sup,
            "contradicted_by": con,
            "depends_on": sorted(deps[cid]),
        }
    return out


def check_claims(
    request: dict[str, Any], ev: dict[str, Evidence], *, allow_cycles: bool = False
) -> dict[str, dict[str, Any]]:
    claims = unique_ids(request.get("claims", []), "Claim")
    for cid, c in claims.items():
        require_refs(c.get("supported_by", []) + c.get("contradicted_by", []), ev, "evidence", f"claim {cid}")
        require_refs(c.get("depends_on", []), claims, "claim", f"claim {cid}")
        overlap = set(c.get("supported_by", [])) & set(c.get("contradicted_by", []))
        if overlap:
            raise CogaError(
                "INVALID_REQUEST",
                f"Claim {cid} lists {sorted(overlap)[0]!r} as both support and contradiction.",
                details={"claim": cid, "evidence": sorted(overlap)},
            )
    if not allow_cycles:
        cycle = find_cycle(list(claims), {k: list(v.get("depends_on", [])) for k, v in claims.items()})
        if cycle:
            raise CogaError(
                "DEPENDENCY_CYCLE",
                f"Claims depend on each other in a cycle: {' -> '.join(cycle)}.",
                details={"cycle": cycle},
            )
    return claims


def run(request: dict[str, Any], ev: dict[str, Evidence]) -> Draft:
    claims = check_claims(request, ev)
    scores = claim_scores(claims, ev)
    rows = [scores[c] for c in sorted(scores)]
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    used = {e for r in rows for e in r["supported_by"] + r["contradicted_by"]}
    draft = Draft(
        result={"claims": rows, "summary": dict(sorted(counts.items())), "unused_evidence": sorted(set(ev) - used)},
        confidence=sum(r["confidence"] for r in rows) / len(rows),
        confidence_basis="mean over claims of |effective support - contradiction|",
        evidence_refs=used,
    )
    for r in rows:
        refs = r["supported_by"] + r["contradicted_by"]
        if r["status"] == "unsupported":
            draft.gap("no-evidence", f"Claim {r['claim_id']} has no evidence either way.", [r["claim_id"]])
        if r["supported_by"] and all(ev[e].kind == "assumption" for e in r["supported_by"]):
            draft.gap("assumption-only", f"Claim {r['claim_id']} is supported only by assumptions.", refs)
        if len(r["supported_by"]) == 1:
            draft.gap("single-source", f"Claim {r['claim_id']} rests on one piece of evidence.", refs)
        if r["status"] == "contested":
            draft.gap("contested", f"Claim {r['claim_id']} has strong evidence on both sides.", refs)
    for e in draft.result["unused_evidence"]:
        draft.note("unused-evidence", f"Evidence {e} is not referenced by any claim.", [e])
    return draft
