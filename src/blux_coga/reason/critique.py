"""reason.critique/1: rule-based critique of claims, tasks and comparisons.

Each rule is exact and documented (docs/REASONING.md#critique-rules); a finding names the rule, a severity
and the ids it concerns. Unlike reason.analyze and reason.plan, cycles are findings here, not errors.
Confidence is 1: the rules are checks, not estimates. The critique says what is weak in the structure,
never whether the conclusion is true.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from blux_coga.reason import compare as compare_mod
from blux_coga.reason.analyze import check_claims, claim_scores
from blux_coga.reason.common import CogaError, Draft, Evidence, find_cycle, require_refs, unique_ids
from blux_coga.reason.plan import check_tasks

RULES = {
    "CR001": ("unsupported-claim", "high"),
    "CR002": ("assumption-only", "high"),
    "CR003": ("single-source", "medium"),
    "CR004": ("contradicted", "high"),
    "CR005": ("circular-claims", "high"),
    "CR006": ("low-reliability", "medium"),
    "CR007": ("unused-evidence", "low"),
    "CR008": ("too-few-options", "medium"),
    "CR009": ("missing-values", "medium"),
    "CR010": ("task-cycle", "high"),
    "CR011": ("unverified-dataset", "low"),
    "CR012": ("duplicate-statement", "low"),
    "CR013": ("depends-on-weak-claim", "medium"),
}


def _norm(text: str) -> str:
    return re.sub(r"\W+", " ", unicodedata.normalize("NFKC", text).casefold()).strip()


def run(request: dict[str, Any], ev: dict[str, Evidence]) -> Draft:
    if not any(request.get(k) for k in ("claims", "tasks", "options")):
        raise CogaError("INVALID_REQUEST", "Nothing to critique: give claims, tasks or options.")
    findings: list[dict[str, Any]] = []

    def hit(rule: str, message: str, refs: list[str]) -> None:
        name, severity = RULES[rule]
        findings.append({"rule": rule, "code": name, "severity": severity, "message": message, "refs": sorted(refs)})

    used: set[str] = set()
    claims = check_claims(request, ev, allow_cycles=True) if request.get("claims") else {}
    if claims:
        deps = {k: list(v.get("depends_on", [])) for k, v in claims.items()}
        cycle = find_cycle(list(claims), deps)
        if cycle:
            hit("CR005", f"Claims support each other in a circle: {' -> '.join(cycle)}.", sorted(set(cycle)))
        scores = claim_scores(claims, ev) if not cycle else {}
        for cid in sorted(claims):
            c = claims[cid]
            sup, con = sorted(c.get("supported_by", [])), sorted(c.get("contradicted_by", []))
            used.update(sup + con)
            if not sup:
                hit("CR001", f"Claim {cid} has no supporting evidence.", [cid])
                continue
            if all(ev[e].kind == "assumption" for e in sup):
                hit("CR002", f"Claim {cid} rests only on assumptions.", [cid, *sup])
            sources = {ev[e].uri or ev[e].id for e in sup}
            if len(sources) == 1:
                hit("CR003", f"All support for claim {cid} comes from one source.", [cid, *sup])
            if con and max(ev[e].reliability for e in con) >= max(ev[e].reliability for e in sup):
                hit(
                    "CR004",
                    f"Claim {cid} is contradicted by evidence at least as reliable as its support.",
                    [cid, *con],
                )
            if max(ev[e].reliability for e in sup) < 0.5:
                hit("CR006", f"Every source supporting claim {cid} has reliability below 0.5.", [cid, *sup])
            for d in sorted(c.get("depends_on", [])):
                if scores and scores[d]["status"] in ("unsupported", "weak", "refuted", "contested"):
                    hit("CR013", f"Claim {cid} depends on claim {d}, which is {scores[d]['status']}.", [cid, d])
        seen: dict[str, str] = {}
        for cid in sorted(claims):
            key = _norm(claims[cid]["statement"])
            if key and key in seen:
                hit("CR012", f"Claims {seen[key]} and {cid} make the same statement.", [seen[key], cid])
            seen.setdefault(key, cid)

    if request.get("tasks"):
        tasks = check_tasks(request, ev)
        used.update(e for t in tasks.values() for e in t.get("evidence", []))
        cycle = find_cycle(list(tasks), {k: list(v.get("depends_on", [])) for k, v in tasks.items()})
        if cycle:
            hit("CR010", f"Tasks depend on each other in a cycle: {' -> '.join(cycle)}.", sorted(set(cycle)))

    if request.get("options"):
        if not request.get("criteria"):
            raise CogaError("INVALID_REQUEST", "Options need criteria to be critiqued.")
        options, criteria = compare_mod.check(request, ev)
        used.update(e for o in options.values() for es in o.get("evidence", {}).values() for e in es)
        if len(options) < 2:
            hit("CR008", "Fewer than two options: there is no alternative to compare against.", sorted(options))
        for oid in sorted(options):
            missing = sorted(c for c in criteria if options[oid].get("values", {}).get(c) is None)
            if missing:
                hit("CR009", f"Option {oid} has no value for {', '.join(missing)}.", [oid, *missing])
    elif request.get("criteria"):
        unique_ids(request["criteria"], "Criterion")

    for eid in sorted(set(ev) - used):
        hit("CR007", f"Evidence {eid} is not used by anything.", [eid])
    for eid in sorted(used):
        e = ev[eid]
        if e.dataset and not (e.dataset.get("sha256") or e.sha256):
            hit("CR011", f"Evidence {eid} cites dataset record {e.dataset['record_id']} without a content hash.", [eid])
    require_refs(sorted(used), ev, "evidence", "critique")

    order = {"high": 0, "medium": 1, "low": 2}
    findings.sort(key=lambda f: (order[f["severity"]], f["rule"], f["refs"]))
    counts = {s: sum(1 for f in findings if f["severity"] == s) for s in ("high", "medium", "low")}
    draft = Draft(
        result={
            "findings": findings,
            "counts": counts,
            "rules": {k: {"code": v[0], "severity": v[1]} for k, v in RULES.items()},
        },
        confidence=1.0,
        confidence_basis="rule checks are exact; they judge the structure, not the truth of any claim",
        evidence_refs=used,
    )
    return draft
