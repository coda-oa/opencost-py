"""Shared fixtures: the openCost schema comes from the vendored upstream repo.

The opencost repository (git submodule at ``vendor/opencost``) is the
authoritative source for the XSD. It is a development-only dependency:
neither the schema files nor validation tooling ship in the wheel.
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
UPSTREAM_DOC = REPO_ROOT / "vendor" / "opencost" / "doc"
SCHEMA_PATH = UPSTREAM_DOC / "opencost.xsd"
EXAMPLES_DIR = UPSTREAM_DOC / "examples"

SKIP_REASON = "opencost submodule not checked out; run `git submodule update --init`"


@pytest.fixture(scope="session")
def schema_path() -> Path:
    if not SCHEMA_PATH.is_file():
        pytest.skip(SKIP_REASON)
    return SCHEMA_PATH


@pytest.fixture(scope="session")
def example_docs() -> list[Path]:
    if not SCHEMA_PATH.is_file():
        pytest.skip(SKIP_REASON)
    return sorted(EXAMPLES_DIR.glob("*.xml"))
