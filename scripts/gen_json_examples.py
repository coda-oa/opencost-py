"""Convert the upstream openCost XML examples to JSON.

Every ``*.xml`` in ``vendor/opencost/doc/examples/`` is parsed with
:func:`opencost.from_xml` and re-serialized with the same wire conventions
the XML serializer uses: field aliases as keys (XSD element names), enums as
their XSD wire values, ``None`` fields omitted (``minOccurs="0"``), Decimal
amounts as strings. The record is wrapped in a top-level ``data`` field,
mirroring the XML root element (``opencost.xsd``) and the upstream JSON
schema. Output is written to ``examples/json/<stem>.json``, regenerated with:

    uv run python scripts/gen_json_examples.py
"""

import json
from pathlib import Path

from opencost import Data, from_xml

EXAMPLES_DIR = Path("vendor/opencost/doc/examples")
OUTPUT_DIR = Path("examples/json")


def to_json(data: Data) -> str:
    """Serialize with wire aliases, omitting unset fields like the XML does."""
    body = json.loads(data.model_dump_json(by_alias=True, exclude_none=True))
    return json.dumps({"data": body}, indent=2, ensure_ascii=False) + "\n"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for xml_path in sorted(EXAMPLES_DIR.glob("*.xml")):
        json_path = OUTPUT_DIR / (xml_path.stem + ".json")
        json_path.write_text(to_json(from_xml(xml_path.read_text())))
        print(f"{xml_path.name} -> {json_path}")


if __name__ == "__main__":
    main()
