"""reason.rank/1: order items from scores or from pairwise preferences.

Scores: descending; equal scores share a rank. Pairwise: for each pair, the net preference weight decides
(win 1, tie 0.5, never compared 0); the Copeland score is the sum, ties broken by total net weight, then id.
Preference cycles (A>B>C>A) and items with no comparisons are reported. Confidence: scores give 1 when no
ranks tie; pairwise gives the share of item pairs that were compared, times the share of adjacent ranks
that are not ties.
"""

from __future__ import annotations

import itertools
from typing import Any

from blux_coga.reason.common import CogaError, Draft, Evidence, find_cycle, require_refs, unique_ids


def _dense(order: list[str], key: dict[str, tuple[float, ...]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rank, last = 0, None
    for i in order:
        if key[i] != last:
            rank += 1
            last = key[i]
        rows.append({"item_id": i, "rank": rank})
    return rows


def run(request: dict[str, Any], ev: dict[str, Evidence]) -> Draft:
    items = unique_ids(request["items"], "Item")
    comps = request.get("comparisons", [])
    scored = [i for i in items.values() if "score" in i]
    if comps and scored:
        raise CogaError("INVALID_REQUEST", "Give item scores or pairwise comparisons, not both.")
    for iid, it in items.items():
        require_refs(it.get("evidence", []), ev, "evidence", f"item {iid}")
    refs = {e for it in items.values() for e in it.get("evidence", [])}

    if not comps:
        if len(scored) != len(items):
            missing = sorted(i for i, it in items.items() if "score" not in it)
            raise CogaError("INVALID_REQUEST", f"Items without a score: {missing[:5]}.", details={"missing": missing})
        score = {i: float(it["score"]) for i, it in items.items()}
        order = sorted(items, key=lambda i: (-score[i], i))
        rows = _dense(order, {i: (score[i],) for i in items})
        for r in rows:
            r["score"] = score[r["item_id"]]
        ties = len(rows) - len({r["rank"] for r in rows})
        draft = Draft(
            result={"mode": "scores", "ranking": rows},
            confidence=1.0 - ties / len(rows),
            confidence_basis="share of items that do not share a rank",
            evidence_refs=refs,
        )
        if ties:
            draft.gap("ties", f"{ties} item(s) share a rank with another.", sorted(r["item_id"] for r in rows))
        return draft

    net: dict[tuple[str, str], float] = {}
    for i, c in enumerate(comps):
        w, lose = c["winner"], c["loser"]
        require_refs([w, lose], items, "item", f"comparisons[{i}]")
        require_refs(c.get("evidence", []), ev, "evidence", f"comparisons[{i}]")
        refs.update(c.get("evidence", []))
        if w == lose:
            raise CogaError("INVALID_REQUEST", f"comparisons[{i}] compares {w} with itself.")
        a, b = sorted((w, lose))
        sign = 1.0 if w == a else -1.0
        net[(a, b)] = net.get((a, b), 0.0) + sign * float(c.get("weight", 1))
    ids = sorted(items)
    copeland = dict.fromkeys(ids, 0.0)
    margin = dict.fromkeys(ids, 0.0)
    beats: dict[str, list[str]] = {i: [] for i in ids}
    for (a, b), v in sorted(net.items()):
        margin[a] += v
        margin[b] -= v
        if v > 0:
            copeland[a] += 1
            beats[a].append(b)
        elif v < 0:
            copeland[b] += 1
            beats[b].append(a)
        else:
            copeland[a] += 0.5
            copeland[b] += 0.5
    order = sorted(ids, key=lambda i: (-copeland[i], -margin[i], i))
    rows = _dense(order, {i: (copeland[i], margin[i]) for i in ids})
    for r in rows:
        r["copeland"] = copeland[r["item_id"]]
        r["net_weight"] = margin[r["item_id"]]
    compared = {x for pair in net for x in pair}
    cycle = find_cycle(ids, beats)
    pairs = len(ids) * (len(ids) - 1) / 2
    ties = sum(1 for x, y in itertools.pairwise(rows) if x["rank"] == y["rank"])
    draft = Draft(
        result={
            "mode": "pairwise",
            "ranking": rows,
            "matrix": [{"pair": [a, b], "net": v} for (a, b), v in sorted(net.items())],
            "preference_cycle": cycle,
        },
        confidence=(len(net) / pairs if pairs else 1.0) * (1.0 - ties / max(1, len(rows) - 1)),
        confidence_basis="share of item pairs compared x share of adjacent ranks that are not ties",
        evidence_refs=refs,
    )
    if cycle:
        draft.gap("preference-cycle", f"Preferences are cyclic: {' > '.join(cycle)}.", sorted(set(cycle)))
    never = sorted(set(ids) - compared)
    if never:
        draft.gap("never-compared", f"{len(never)} item(s) were never compared.", never)
    if len(net) < pairs:
        draft.gap("incomplete-comparisons", f"{int(pairs) - len(net)} of {int(pairs)} pairs were not compared.", [])
    return draft
