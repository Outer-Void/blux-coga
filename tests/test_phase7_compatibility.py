from blux_coga.contracts.models import RunHeader
from blux_coga.io import cli


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


def test_only_documented_legacy_cli_alias_is_supported():
    parser = cli._build_parser()
    args = parser.parse_args(["run", "--in", "problem.json", "--out", "out"])
    assert str(args.input) == "problem.json"
    assert str(args.output_dir) == "out"
