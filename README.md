# opencost

Pydantic models for the [openCost](https://github.com/opencost-de/opencost)
metadata schema — a schema for the **financial** metadata of scholarly
publications — plus a serializer that emits schema-valid openCost XML.

openCost describes two top-level entities, both collectable in one
`opencost:data` document:

- `publication` — a single article (or other publication) and its costs:
  identifiers, paying institution, COAR publication type, and `cost_data`
  (invoices with itemized amounts, or a link to a contract).
- `contract` — payment models such as transformative agreements,
  memberships, or subscriptions, with grouped invoices per accounting period.

## Install

```bash
uv add opencost   # or: pip install opencost
```

## Usage

### Building documents

```python
from decimal import Decimal

import opencost

publication = opencost.PublicationType(
    primary_identifier=opencost.PublicationPrimaryIdentifier(doi="10.1234/abcd"),
    institution=opencost.InstitutionType(
        id=[opencost.InstitutionId(type="ror", value="010zzcb52")]
    ),
    publication_type=opencost.CoarPublicationType.journal_article,
    cost_data=opencost.PublicationCostDataType(
        invoice=[
            opencost.PublicationInvoiceType(
                invoice_number="INV-4711",
                creditor="Publisher GmbH",
                dates=opencost.Dates(invoice="2026-05-01", paid="2026-05-20"),
                amount_invoice=opencost.AmountInvoice(
                    amount=Decimal("1980.00"), currency="EUR"
                ),
                amounts_paid=opencost.PublicationAmountsPaid(
                    amount_paid=[
                        opencost.PublicationAmountPaidType(
                            amount=Decimal("1650.00"),
                            currency="EUR",
                            cost_type="gold-oa",
                            vat=Decimal("342.00"),
                        )
                    ]
                ),
            )
        ]
    ),
)

xml = opencost.to_xml(opencost.Data(publication=[publication]))
```

which produces

```xml
<data xmlns="https://opencost.de">
  <publication>
    <primary_identifier>
      <doi>10.1234/abcd</doi>
    </primary_identifier>
    ...
  </publication>
</data>
```

### Parsing documents

`from_xml` is the exact inverse — children are matched to fields by
element name, and every value is validated through the same models:

```python
from pathlib import Path

data = opencost.from_xml(Path("report.xml").read_text())

for publication in data.publication or []:
    doi = publication.primary_identifier.doi
    for invoice in publication.cost_data.invoice or []:
        for amount in invoice.amounts_paid.amount_paid:
            print(doi, amount.amount, amount.currency, amount.cost_type.value)
```

Parsed values are fully typed (`Decimal` amounts, enum members, `bool`s),
unknown elements are rejected, and the round-trip is lossless:
`from_xml(to_xml(d)) == d`.

## Validation

The models enforce the schema rules that can be expressed as type
constraints:

- required lists (`Annotated[list[T], Field(min_length=1)]`) reject empty
  lists — e.g. `PublicationSecondaryIdentifiers(id=[])` fails;
- either/or rules (`EitherFieldMixin`) — e.g. `Dates` needs `invoice` or
  `paid`, `Data` needs `publication` or `contract`;
- exactly-one rules — `PublicationPrimaryIdentifier` takes a `doi` **or** a
  `bibliographic_information` block, never both or neither;
- patterns — `Currency` is a three-letter ISO 4217 code, `DateFormat` is
  `YYYY`, `YYYY-MM` or `YYYY-MM-DD`;
- strict model config — unknown/misspelled fields are rejected
  (`extra="forbid"`), and aliased fields accept both the Python name and
  the wire alias (`from_` or `from`).

### Validating generated documents

The XSD is owned by the upstream [opencost repository](https://github.com/opencost-de/opencost)
(`doc/opencost.xsd`). This package deliberately does **not** ship a copy —
validate generated documents against the upstream schema, e.g. with
[xmllint](https://xmlsoft.org/xmllint.html):

```bash
xmllint --noout --schema path/to/opencost/doc/opencost.xsd data.xml
```

In this repository the upstream schema is pinned as a git submodule
(`vendor/opencost`) and used by the test suite — it is a development-only
dependency, never a runtime one.

## XML (de)serialization

`to_xml` derives the XML shape from the models themselves:

- field declaration order → child order (deterministic; the XSD uses
  `xs:all`/symmetric choices, so order is not semantically constrained);
- `None` → element omitted (`minOccurs=0`);
- `list` → repeated sibling elements (`maxOccurs="unbounded"`);
- field `alias` → element name (e.g. `from_` → `<from>`);
- enums → their XSD wire values (`journal article`, `gold-oa`);
- `bool` → `true`/`false`; `Decimal` → two decimal places.

`from_xml` is the exact inverse — the models drive parsing too: children
are matched to fields by element name, type coercion (Decimal, booleans,
enum-by-value, patterns) is pydantic's job, and unknown elements are
rejected via `extra="forbid"`. Documents with the default namespace or an
`opencost:` prefix parse identically. Round-trip stable:
`from_xml(to_xml(d)) == d`.

```python
data = opencost.from_xml(Path("report.xml").read_text())
for pub in data.publication or []:
    ...
```

## Development

```bash
git submodule update --init   # pins upstream schema for the validation tests
uv sync
uv run pytest
```

## License

GPL-3.0-or-later.

