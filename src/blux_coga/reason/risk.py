"""reason.risk/1: inherent and residual risk.

score      = likelihood (0-1) x impact (0-5), so 0-5
residual   = likelihood x product(1 - reduction) of likelihood mitigations
             x impact x product(1 - reduction) of impact mitigations
band       = low < 1 <= medium < 2 <= high < 3.5 <= critical      (on the residual score)
appetite   = residual score above which a risk is "over appetite" (default 2.0)
Confidence = share of risks whose likelihood cites evidence.
"""

from __future__ import annotations

from typing import Any

from blux_coga.reason.common import Draft, Evidence, require_refs, unique_ids

BANDS = ((1.0, "low"), (2.0, "medium"), (3.5, "high"))


def band(score: float) -> str:
    for limit, name in BANDS:
        if score < limit:
            return name
    return "critical"


def run(request: dict[str, Any], ev: dict[str, Evidence]) -> Draft:
    risks = unique_ids(request["risks"], "Risk")
    appetite = float(request.get("appetite", 2.0))
    rows: list[dict[str, Any]] = []
    refs: set[str] = set()
    for rid in sorted(risks):
        r = risks[rid]
        require_refs(r.get("evidence", []), ev, "evidence", f"risk {rid}")
        mitigations = unique_ids(r.get("mitigations", []), f"Mitigation of {rid}")
        lk, im = float(r["likelihood"]), float(r["impact"])
        lk_res, im_res = lk, im
        for mid in sorted(mitigations):
            m = mitigations[mid]
            require_refs(m.get("evidence", []), ev, "evidence", f"risk {rid} mitigation {mid}")
            refs.update(m.get("evidence", []))
            if m["applies_to"] == "likelihood":
                lk_res *= 1.0 - float(m["reduction"])
            else:
                im_res *= 1.0 - float(m["reduction"])
        refs.update(r.get("evidence", []))
        inherent, residual = lk * im, lk_res * im_res
        rows.append(
            {
                "risk_id": rid,
                "likelihood": lk,
                "impact": im,
                "inherent": inherent,
                "inherent_band": band(inherent),
                "residual_likelihood": lk_res,
                "residual_impact": im_res,
                "residual": residual,
                "residual_band": band(residual),
                "reduction": inherent - residual,
                "over_appetite": residual > appetite,
                "mitigations": sorted(mitigations),
            }
        )
    ranking = [r["risk_id"] for r in sorted(rows, key=lambda r: (-r["residual"], r["risk_id"]))]
    result: dict[str, Any] = {
        "appetite": appetite,
        "risks": rows,
        "ranking": ranking,
        "over_appetite": [r["risk_id"] for r in rows if r["over_appetite"]],
        "total_inherent": sum(r["inherent"] for r in rows),
        "total_residual": sum(r["residual"] for r in rows),
        "worst": ranking[0],
        "bands": {b: sum(1 for r in rows if r["residual_band"] == b) for b in ("low", "medium", "high", "critical")},
    }
    evidenced = [rid for rid, r in risks.items() if r.get("evidence")]
    draft = Draft(
        result=result,
        confidence=len(evidenced) / len(risks),
        confidence_basis="share of risks whose likelihood cites evidence",
        evidence_refs=refs,
    )
    bare = sorted(set(risks) - set(evidenced))
    if bare:
        draft.gap("unsupported-likelihood", f"{len(bare)} risk(s) estimate likelihood without evidence.", bare)
    unverified = sorted(
        f"{rid}/{m['id']}" for rid, r in risks.items() for m in r.get("mitigations", []) if not m.get("evidence")
    )
    if unverified:
        draft.gap(
            "unverified-mitigation", f"{len(unverified)} mitigation(s) cite no evidence of their effect.", unverified
        )
    for rid in result["over_appetite"]:
        draft.note(
            "over-appetite", f"Risk {rid} stays above the appetite of {appetite} after mitigation.", [rid], "high"
        )
    return draft
