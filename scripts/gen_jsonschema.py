"""Emit the openCost JSON schema to stdout.

The schema body is derived from the pydantic models rooted at
``opencost.Data`` (``model_json_schema``, wire aliases kept); the header
is the openCost JSON schema envelope - ``$id`` is the schema's XML
targetNamespace, so validators referencing ``https://opencost.de`` pick
this document up as the JSON counterpart of the XSD. Regenerate the
checked-in artifact with:

    uv run python scripts/gen_jsonschema.py > schema.json
"""

import json
from collections import OrderedDict

import opencost


def build_schema() -> dict[str, object]:
    """Envelope header first; pydantic contributes the ``data`` body.

    The root mirrors the XML document shape: a single ``data`` property
    (the XSD root element, ``opencost.xsd``) holding ``Data``'s schema —
    including its ``anyOf`` mirroring the either/or rule (``publication``
    or ``contract``) from ``EitherFieldMixin``. ``$defs`` stay at the root,
    where JSON Schema references resolve.
    """
    envelope = OrderedDict(
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "https://opencost.de",
            "title": "openCost JSON Schema",
            "description": (
                "Validates openCost records in JSON. Automatically transformed "
                "from the pydantic models based on the original openCost XSD Schema."
            ),
            "type": "object",
            "additionalProperties": False,
            "required": ["data"],
        }
    )
    data_schema = OrderedDict(opencost.Data.model_json_schema(by_alias=True))
    defs = data_schema.pop("$defs", None)
    if defs:
        envelope["$defs"] = defs
    envelope["properties"] = OrderedDict({"data": data_schema})
    return envelope


def main() -> None:
    print(json.dumps(build_schema(), indent=2))


if __name__ == "__main__":
    main()
