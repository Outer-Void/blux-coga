"""reason.decompose/1: the structure of a goal's work breakdown.

Items form a tree under the goal through `parent` (roots hang off the goal). Reported: depth of each item,
leaves, work packages (connected components over parent and depends_on links), acceptance coverage (each
acceptance criterion is covered when an item it names, or a descendant of one, exists), and untraced items
(neither covering a criterion nor under or above an item that does). Confidence = share of acceptance
criteria covered (1 when there are none, with the absence reported).
"""

from __future__ import annotations

from typing import Any

from blux_coga.reason.common import CogaError, Draft, Evidence, find_cycle, require_refs, unique_ids


def run(request: dict[str, Any], ev: dict[str, Evidence]) -> Draft:
    goal = request["goal"]
    items = unique_ids(request["items"], "Item")
    for iid, it in items.items():
        if "parent" in it:
            require_refs([it["parent"]], items, "item", f"item {iid} parent")
        require_refs(it.get("depends_on", []), items, "item", f"item {iid}")
    parents = {iid: [it["parent"]] if "parent" in it else [] for iid, it in items.items()}
    cycle = find_cycle(list(items), parents)
    if cycle:
        raise CogaError(
            "DEPENDENCY_CYCLE", f"Item parents form a cycle: {' -> '.join(cycle)}.", details={"cycle": cycle}
        )
    acceptance = unique_ids(goal.get("acceptance", []), "Acceptance criterion")
    for aid, a in acceptance.items():
        require_refs(a.get("covered_by", []), items, "item", f"acceptance {aid}")

    children: dict[str, list[str]] = {iid: [] for iid in items}
    for iid, it in items.items():
        if "parent" in it:
            children[it["parent"]].append(iid)
    depth: dict[str, int] = {}

    def d(i: str) -> int:
        if i not in depth:
            p = items[i].get("parent")
            depth[i] = 1 if p is None else d(p) + 1
        return depth[i]

    for iid in sorted(items):
        d(iid)

    def descendants(i: str) -> set[str]:
        out: set[str] = set()
        stack = list(children[i])
        while stack:
            n = stack.pop()
            if n not in out:
                out.add(n)
                stack.extend(children[n])
        return out

    def ancestors(i: str) -> set[str]:
        out: set[str] = set()
        p = items[i].get("parent")
        while p is not None:
            out.add(p)
            p = items[p].get("parent")
        return out

    # work packages: connected components over parent and dependency links (undirected)
    adj: dict[str, set[str]] = {iid: set() for iid in items}
    for iid, it in items.items():
        for other in ([it["parent"]] if "parent" in it else []) + list(it.get("depends_on", [])):
            adj[iid].add(other)
            adj[other].add(iid)
    seen: set[str] = set()
    packages: list[list[str]] = []
    for iid in sorted(items):
        if iid in seen:
            continue
        comp, stack = set(), [iid]
        while stack:
            n = stack.pop()
            if n not in comp:
                comp.add(n)
                stack.extend(adj[n])
        seen |= comp
        packages.append(sorted(comp))

    coverage: list[dict[str, Any]] = []
    traced: set[str] = set()
    for aid in sorted(acceptance):
        covering = sorted(acceptance[aid].get("covered_by", []))
        for c in covering:
            traced |= {c} | descendants(c) | ancestors(c)
        coverage.append({"acceptance_id": aid, "covered_by": covering, "covered": bool(covering)})
    uncovered = [c["acceptance_id"] for c in coverage if not c["covered"]]
    untraced = sorted(set(items) - traced) if acceptance else []

    result = {
        "goal": {"id": goal.get("id"), "statement": goal["statement"]},
        "tree": [
            {"item_id": i, "parent": items[i].get("parent"), "depth": depth[i], "children": sorted(children[i])}
            for i in sorted(items)
        ],
        "roots": sorted(i for i in items if "parent" not in items[i]),
        "leaves": sorted(i for i in items if not children[i]),
        "max_depth": max(depth.values()),
        "work_packages": packages,
        "acceptance": coverage,
        "uncovered_acceptance": uncovered,
        "untraced_items": untraced,
    }
    draft = Draft(
        result=result,
        confidence=(len(acceptance) - len(uncovered)) / len(acceptance) if acceptance else 1.0,
        confidence_basis="share of acceptance criteria covered by at least one item",
    )
    if not acceptance:
        draft.gap("no-acceptance-criteria", "The goal has no acceptance criteria, so coverage cannot be judged.")
    if uncovered:
        draft.gap("uncovered-acceptance", f"{len(uncovered)} acceptance criteria are covered by no item.", uncovered)
    if untraced:
        draft.note("untraced-items", f"{len(untraced)} item(s) trace to no acceptance criterion.", untraced)
    return draft
