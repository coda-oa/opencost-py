"""Deserialization: XML -> openCost domain models.

The exact inverse of ``_serialize``: the pydantic models drive parsing
too, and all type coercion is delegated to pydantic.
"""

from __future__ import annotations

import types
from typing import Any, Union, get_args, get_origin
from xml.etree import ElementTree as ET

from pydantic import BaseModel

from .._common import Data
from ._common import NAMESPACE


def _tag(elem: ET.Element) -> str:
    """Element name for matching against fields.

    The openCost namespace (and no namespace at all) map to the local
    name, so default-xmlns and ``opencost:``-prefixed documents agree.
    Any *foreign* namespace keeps its qualified form, which can never
    match a field name and is therefore rejected as an unknown element.
    """
    ns, sep, local = elem.tag.rpartition("}")
    if not sep or ns == "{":
        return local
    if ns[1:] == NAMESPACE:
        return local
    return elem.tag


def _root_tag_ok(root: ET.Element) -> bool:
    ns, sep, local = root.tag.rpartition("}")
    if sep and ns[1:] not in ("", NAMESPACE):
        return False
    return local == "data"


def _strip_annotated(annotation: Any) -> Any:
    while getattr(annotation, "__metadata__", None) is not None:
        annotation = get_args(annotation)[0]
    return annotation


def _unwrap_optional(annotation: Any) -> Any:
    annotation = _strip_annotated(annotation)
    origin = get_origin(annotation)
    if origin is Union or origin is types.UnionType:
        args = [_strip_annotated(a) for a in get_args(annotation) if a is not types.NoneType]
        if len(args) != 1:
            raise TypeError(f"unsupported union in schema model: {annotation!r}")
        annotation = args[0]
    return _strip_annotated(annotation)


def _leaf_text(elem: ET.Element) -> str | None:
    """Text of a scalar element; nested markup is rejected, not dropped.

    ``found[0].text`` alone would silently discard child elements and
    their tails (e.g. ``<doi><value>…</value></doi>`` yielding pure
    whitespace that passes ``NonEmptyString``); xmllint rejects such
    documents, so we must too.
    """
    if len(elem):
        raise ValueError(f"element <{elem.tag}> must contain text, not child elements")
    return elem.text


def _parse_element(model_cls: type[BaseModel], elem: ET.Element) -> dict[str, Any]:
    """Build a validation-ready mapping for ``model_cls`` from one element.

    Mirrors ``_element`` in reverse: each model field claims the children
    named after its wire name (alias or field name); model children
    recurse, repeated children become lists, everything else contributes
    its raw text. All type coercion (Decimal, xsd boolean strings,
    enum-by-value, string patterns) is left to pydantic.

    Keys are the *wire* names, so a child tagged with a Python field name
    (e.g. ``<from_>``) can never overwrite the field parsed from its wire
    element (``<from>``); it lands in the extras path instead. Children
    that match no wire name are passed through under their own tag so the
    models' ``extra="forbid"`` config rejects them loudly -- including
    foreign-namespace tags (see ``_tag``). Child *order is irrelevant*
    (the XSD uses ``xs:all``/symmetric choices); a repeated
    single-cardinality child beyond the first is ignored, which only ever
    occurs in documents that xmllint rejects anyway.
    """
    children: dict[str, list[ET.Element]] = {}
    for child in elem:
        children.setdefault(_tag(child), []).append(child)

    values: dict[str, Any] = {}
    known: set[str] = set()
    for field_name, field in model_cls.model_fields.items():
        wire = field.alias or field_name
        known.add(wire)
        found = children.get(wire)
        if not found:
            # Absent child stays absent: pydantic reports genuinely
            # missing required fields; optional ones fall back to None.
            continue
        target = _unwrap_optional(field.annotation)
        if get_origin(target) is list:
            (item_type,) = get_args(target)
            if isinstance(item_type, type) and issubclass(item_type, BaseModel):
                values[wire] = [_parse_element(item_type, c) for c in found]
            else:
                values[wire] = [_leaf_text(c) for c in found]
        elif isinstance(target, type) and issubclass(target, BaseModel):
            values[wire] = _parse_element(target, found[0])
        else:
            values[wire] = _leaf_text(found[0])

    for tag_name, elems in children.items():
        if tag_name not in known:
            # Unknown element: hand it to pydantic as an extra key; every
            # openCost model forbids extras, so this raises extra_forbidden.
            values[tag_name] = _leaf_text(elems[0])
    return values


def from_xml(source: str | bytes) -> Data:
    """Parse an openCost XML document into the domain models.

    Accepts documents in the openCost namespace (default xmlns or
    ``opencost:`` prefix) or with no namespace; foreign-namespace elements
    are rejected as unknown. Schema validity is checked by pydantic plus
    the models' constraints, not by the XSD.
    """
    root = ET.fromstring(source)
    if not _root_tag_ok(root):
        raise ValueError(f"expected root element 'data', found '{root.tag}'")
    # by_name=False: construction accepts both spellings, but XML is the
    # wire format -- only element names (aliases) may fill a field, so a
    # stray <from_> is rejected as an unknown element, never merged.
    return Data.model_validate(_parse_element(Data, root), by_name=False)
