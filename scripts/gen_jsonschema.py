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
    """Envelope header first; pydantic contributes $defs and properties.

    Overlapping top-level keys (``title``, ``type``,
    ``additionalProperties``) resolve in favor of the header. There is no
    top-level ``required``: ``Data``'s either/or rule (``publication`` or
    ``contract``) is a model validator, not expressible as ``required``.
    """
    json_schema = OrderedDict(
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
        }
    )
    merged = OrderedDict(json_schema)
    for key, value in opencost.Data.model_json_schema(by_alias=True).items():
        if key not in merged:
            merged[key] = value
    return merged


def main() -> None:
    print(json.dumps(build_schema(), indent=2))


if __name__ == "__main__":
    main()
