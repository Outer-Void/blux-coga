from blux_coga.contracts.models import RunHeader


def test_run_header_backfills_missing_fields():
    legacy_payload = {
        "input_hash": "hash",
        "contract_version": "0.4",
        "model_version": "CogA-0.4",
    }
    header = RunHeader.from_dict(legacy_payload)
    assert header.input_hash == "hash"
    assert header.reasoning_pack_id == "unknown"
    assert header.schema_version == "unknown"
