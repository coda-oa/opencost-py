"""Generate src/opencost/_coar.py from the pinned openCost XSD.

The openCost schema enumerates every COAR v3.2 publication type in three
wire spellings per concept (English label, https PURL, http PURL); the
resulting 306-member enumeration is machine-owned vocabulary, not
hand-maintained code. Run this after bumping the vendor/opencost submodule
pin and commit the regenerated module together with the pin:

    uv run python scripts/gen_coar.py

The nox session ``vocab_sync`` checks drift with ``--check`` (no writes).
"""

import argparse
import keyword
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
XSD = ROOT / "vendor" / "opencost" / "doc" / "opencost_types.xsd"
TARGET = ROOT / "src" / "opencost" / "_coar.py"
XS = "http://www.w3.org/2001/XMLSchema"


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def read_concepts() -> list[tuple[str, str, str]]:
    """(label, https_purl, http_purl) per concept, in XSD order.

    The schema lists each concept as three enumerations: http PURL, https
    PURL, then the label.
    """
    root = ET.parse(XSD).getroot()
    (simple_type,) = (
        s for s in root.findall(f"{{{XS}}}simpleType") if s.get("name") == "coar_publication_type"
    )
    values = [e.get("value") for e in simple_type.iter(f"{{{XS}}}enumeration")]
    if len(values) % 3:
        sys.exit(f"unexpected coar_publication_type size: {len(values)}")
    concepts = []
    for i in range(0, len(values), 3):
        http_purl, https_purl, label = values[i : i + 3]
        if not (
            http_purl.startswith("http://purl.org/coar/resource_type/")
            and https_purl.startswith("https://purl.org/coar/resource_type/")
        ):
            sys.exit(f"unexpected enumeration order at index {i}: {values[i : i + 3]}")
        concepts.append((label, https_purl, http_purl))
    return concepts


def render(concepts: list[tuple[str, str, str]], pin: str) -> str:
    lines = [
        '"""COAR controlled vocabulary (v3.2) publication types.',
        "",
        "GENERATED FILE - do not edit.",
        "Source: vendor/opencost/doc/opencost_types.xsd, simpleType",
        f"``coar_publication_type``, submodule pin {pin}.",
        "Regenerate with: uv run python scripts/gen_coar.py",
        '"""',
        "",
        "from enum import Enum",
        "",
        "",
        "class CoarPublicationType(Enum):",
        '    """Publication type as the reporting institution categorizes it (§5).',
        "",
        "    Members are the COAR controlled vocabulary (v3.2) English labels plus the",
        "    corresponding COAR PURLs in both `https` (``*_purl``) and `http`",
        "    (``*_purl_http``) spellings - matching the openCost schema enumeration",
        "    exactly. PURLs are recommended as language-independent persistent",
        "    identifiers; a document parsed with an `http` PURL re-serializes with",
        "    `http` unchanged.",
        '    """',
        "",
    ]
    for label, https_purl, http_purl in concepts:
        name = slug(label)
        lines.append(f'    {name} = "{label}"')
        lines.append(f'    {name}_purl = "{https_purl}"')
        lines.append(f'    {name}_purl_http = "{http_purl}"')
    return "\n".join(lines) + "\n"


def check_member_names(concepts: list[tuple[str, str, str]]) -> None:
    """Fail loudly at generation time, not at import time.

    Enum rejects duplicate members when the module loads; identifiers that
    are keywords or start with a digit fail at parse time. The generated
    vocabulary must never produce either.
    """
    seen: set[str] = set()
    for label, _, _ in concepts:
        base = slug(label)
        for name in (base, f"{base}_purl", f"{base}_purl_http"):
            if not name.isidentifier() or keyword.iskeyword(name):
                sys.exit(f"label {label!r} derives invalid member name {name!r}")
            if name in seen:
                sys.exit(f"duplicate member name {name!r} from label {label!r}")
            seen.add(name)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Regenerate src/opencost/_coar.py from the pinned openCost XSD."
    )
    parser.add_argument(
        "--check", action="store_true", help="fail on drift without writing"
    )
    args = parser.parse_args()
    # Check the XSD first: without a checked-out submodule, git commands
    # here would silently resolve to the SUPERPROJECT's HEAD.
    if not XSD.is_file():
        sys.exit(f"missing {XSD}; run `git submodule update --init`")
    # Full sha: --short is a *minimum* width and can widen after a fetch,
    # which would alter the header and trip vocab_sync without any change
    # in vocabulary.
    pin = subprocess.run(
        ["git", "-C", str(XSD.parent.parent), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    concepts = read_concepts()
    check_member_names(concepts)
    text = render(concepts, pin)
    try:
        compile(text, str(TARGET), "exec")
    except SyntaxError as exc:  # pragma: no cover - vocabulary should never do this
        sys.exit(f"generated module does not compile: {exc}")
    if args.check:
        current = TARGET.read_text() if TARGET.is_file() else None
        if current != text:
            sys.exit(
                f"{TARGET.relative_to(ROOT)} drifted from pin {pin}; "
                "run `uv run python scripts/gen_coar.py` to regenerate"
            )
        print(f"{TARGET.relative_to(ROOT)} is in sync with pin {pin}")
    else:
        TARGET.write_text(text)
        print(f"wrote {TARGET.relative_to(ROOT)} from pin {pin}")


if __name__ == "__main__":
    main()
