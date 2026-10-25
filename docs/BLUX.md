# CogA through BLUX

CogA is `role: standalone` and imports nothing from BLUX. Its `.blux/` declares the seven `reason.*`
capabilities:

- `side_effects: none`, no permissions;
- `provider.kind: subprocess`, `entrypoint: coga blux-capability <id>` (ADR-0009);
- `input_schema` and `output_schema` are the very JSON Schemas CogA validates against. They are generated
  into `.blux/capabilities.yaml` by `scripts/gen_schemas.py`, and a test fails if they drift.

So BLUX validates every request before CogA sees it, and every artifact after. The default policy allows
all actor types, because the capabilities have no side effects.

| CogA | BLUX result | BLUX System |
|---|---|---|
| artifact produced | `succeeded`; `output` is the `coga.artifact`, with `linkage` naming the operation | `SUCCESS` receipt: `input_sha256` = request hash, `output_sha256` = artifact hash |
| request rejected (`INVALID_REQUEST`, `DEPENDENCY_CYCLE` …) | `failed`, `EXECUTION_FAILED`, `details.provider_code` = CogA's code | `FAILURE` |

## Replay through BLUX System

The receipt fixes the hashes of the request and of the exact artifact BLUX returned. To prove a stored result
reproduces:

```bash
blux run reason.compare --project path/to/blux-coga --input "$(cat req.json)" --system-store truth > r.json
jq .output r.json > art.json
coga replay art.json --request req.json -o recomputed.json     # recompute; linkage is preserved
blux-system replay-check "$(jq -r .operation_id r.json)" --store truth --input req.json --output recomputed.json
# {"input_match": true, "output_match": true, "ok": true, ...}
```

`artifact_id` excludes `linkage`, so the same request run in a later operation gets the same `artifact_id`,
and the two operations can be linked by it. BLUX's `tests/integration/test_coga.py` runs this as the
Stage 06 hard gate.
