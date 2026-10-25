"""reason.plan/1: dependency order, stages, critical path and slack.

Tasks without an effort count as 1 (reported as uncertainty). Stage n holds tasks whose longest dependency
chain has n-1 links. Earliest start = max earliest finish of dependencies; the critical path is the longest
effort path (ties: smaller ids); slack = latest start - earliest start. With max_parallel, a list schedule
(ready tasks by earliest start, then id) gives a makespan under that width.
"""

from __future__ import annotations

from typing import Any

from blux_coga.reason.common import CogaError, Draft, Evidence, find_cycle, require_refs, topo_order, unique_ids


def check_tasks(request: dict[str, Any], ev: dict[str, Evidence]) -> dict[str, dict[str, Any]]:
    tasks = unique_ids(request.get("tasks", []), "Task")
    for tid, t in tasks.items():
        require_refs(t.get("depends_on", []), tasks, "task", f"task {tid}")
        require_refs(t.get("evidence", []), ev, "evidence", f"task {tid}")
        if tid in t.get("depends_on", []):
            raise CogaError("DEPENDENCY_CYCLE", f"Task {tid} depends on itself.", details={"cycle": [tid, tid]})
    return tasks


def run(request: dict[str, Any], ev: dict[str, Evidence]) -> Draft:
    tasks = check_tasks(request, ev)
    deps = {tid: sorted(t.get("depends_on", [])) for tid, t in tasks.items()}
    cycle = find_cycle(list(tasks), deps)
    if cycle:
        raise CogaError(
            "DEPENDENCY_CYCLE",
            f"Tasks depend on each other in a cycle: {' -> '.join(cycle)}.",
            details={"cycle": cycle},
        )
    order = topo_order(list(tasks), deps)
    effort = {tid: float(t.get("effort", 1)) for tid, t in tasks.items()}
    level: dict[str, int] = {}
    es: dict[str, float] = {}
    ef: dict[str, float] = {}
    prev: dict[str, str | None] = {}
    for tid in order:
        level[tid] = 1 + max((level[d] for d in deps[tid]), default=0)
        best = None
        for d in deps[tid]:
            if best is None or ef[d] > ef[best] or (ef[d] == ef[best] and d < best):
                best = d
        prev[tid] = best
        es[tid] = ef[best] if best is not None else 0.0
        ef[tid] = es[tid] + effort[tid]
    makespan = max(ef.values())
    dependents: dict[str, list[str]] = {tid: [] for tid in tasks}
    for tid, ds in deps.items():
        for d in ds:
            dependents[d].append(tid)
    lf: dict[str, float] = {}
    for tid in reversed(order):
        lf[tid] = min((lf[n] - effort[n] for n in dependents[tid]), default=makespan)
    end = min((t for t in tasks if ef[t] == makespan), key=lambda t: t)
    path = [end]
    while prev[path[-1]] is not None:
        path.append(prev[path[-1]])  # type: ignore[arg-type]
    path.reverse()

    stages = [sorted(t for t in tasks if level[t] == n) for n in range(1, max(level.values()) + 1)]
    schedule = [
        {
            "task_id": tid,
            "stage": level[tid],
            "effort": effort[tid],
            "earliest_start": es[tid],
            "earliest_finish": ef[tid],
            "latest_start": lf[tid] - effort[tid],
            "slack": lf[tid] - effort[tid] - es[tid],
            "critical": tid in path,
        }
        for tid in order
    ]
    result: dict[str, Any] = {
        "goal": request.get("goal"),
        "order": order,
        "stages": stages,
        "critical_path": {"tasks": path, "length": makespan},
        "schedule": schedule,
        "makespan": makespan,
    }
    if "max_parallel" in request:
        result["parallel"] = _list_schedule(order, deps, effort, es, int(request["max_parallel"]))

    estimated = [t for t in tasks.values() if "effort" in t]
    draft = Draft(
        result=result,
        confidence=len(estimated) / len(tasks),
        confidence_basis="fraction of tasks with an explicit effort",
        evidence_refs={e for t in tasks.values() for e in t.get("evidence", [])},
    )
    defaulted = sorted(tid for tid, t in tasks.items() if "effort" not in t)
    if defaulted:
        draft.gap("default-effort", f"{len(defaulted)} task(s) have no effort; 1 was assumed.", defaulted)
    unsupported = sorted(tid for tid, t in tasks.items() if not t.get("evidence"))
    if unsupported and len(unsupported) < len(tasks):
        draft.note("task-without-evidence", f"{len(unsupported)} task(s) cite no evidence.", unsupported)
    return draft


def _list_schedule(
    order: list[str], deps: dict[str, list[str]], effort: dict[str, float], es: dict[str, float], width: int
) -> dict[str, Any]:
    finish: dict[str, float] = {}
    running: list[tuple[float, str]] = []  # (finish, task)
    pending = list(order)
    clock = 0.0
    starts: dict[str, float] = {}
    while pending:
        ready = [t for t in pending if all(d in finish and finish[d] <= clock for d in deps[t])]
        ready.sort(key=lambda t: (es[t], t))
        while ready and len(running) < width:
            t = ready.pop(0)
            pending.remove(t)
            starts[t] = clock
            running.append((clock + effort[t], t))
        running.sort()
        if not running:  # pragma: no cover - impossible without a cycle
            break
        clock, done = running.pop(0)
        finish[done] = clock
        while running and running[0][0] == clock:
            finish[running.pop(0)[1]] = clock
    for f, t in running:
        finish[t] = f
    return {
        "max_parallel": width,
        "makespan": max(finish.values()),
        "starts": [
            {"task_id": t, "start": starts[t], "finish": finish[t]}
            for t in sorted(starts, key=lambda t: (starts[t], t))
        ],
    }
