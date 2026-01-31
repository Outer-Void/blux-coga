from pathlib import Path

from blux_coga.contracts.reasoning_packs import load_reasoning_pack


def test_reasoning_pack_loads_from_repo():
    base_dir = Path(__file__).resolve().parents[1]
    pack = load_reasoning_pack("default", base_dir / "reasoning_packs")
    assert pack.pack_id == "default"
    assert pack.version
