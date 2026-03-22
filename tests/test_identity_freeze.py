import json
from pathlib import Path

import blux_coga
from blux_coga.core.constants import (
    CONTRACT_VERSION,
    DEFAULT_REASONING_PACK_ID,
    MODEL_VERSION,
    PACKAGE_NAME,
    PACKAGE_VERSION,
    SCHEMA_VERSION,
)


def test_package_identity_is_frozen_and_coherent() -> None:
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    pyproject_text = pyproject.read_text(encoding="utf-8")

    assert f'name = "{PACKAGE_NAME}"' in pyproject_text
    assert f'version = "{PACKAGE_VERSION}"' in pyproject_text
    assert blux_coga.__version__ == PACKAGE_VERSION
    assert MODEL_VERSION == "CogA-1.0-pro"
    assert CONTRACT_VERSION == "1.0"
    assert SCHEMA_VERSION == "1.0"
    assert DEFAULT_REASONING_PACK_ID == "default"


def test_default_reasoning_pack_version_matches_frozen_docs() -> None:
    pack_path = Path(__file__).resolve().parents[1] / "reasoning_packs" / "default.json"
    payload = json.loads(pack_path.read_text(encoding="utf-8"))

    assert payload["id"] == DEFAULT_REASONING_PACK_ID
    assert payload["version"] == "1.0"
