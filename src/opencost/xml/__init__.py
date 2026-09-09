"""XML (de)serialization for the openCost domain models.

Both directions are driven by the pydantic models themselves:

- :func:`to_xml` renders a :class:`opencost.Data` document as XML;
- :func:`from_xml` parses an XML document back into the models.

Both are re-exported from the top-level ``opencost`` package.
"""

from ._common import NAMESPACE as NAMESPACE
from ._deserialize import from_xml as from_xml
from ._serialize import to_xml as to_xml

__all__ = [
    "NAMESPACE",
    "from_xml",
    "to_xml",
]
