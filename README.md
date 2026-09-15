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

The rules the models enforce split in two: restrictions the upstream XSD
mandates, which the models mirror as type constraints, and two date checks
this package adds on top.

### Mandated by the schema

- required lists — `Annotated[list[T], Field(min_length=1)]` rejects an empty
  list wherever the XSD declares `minOccurs="1" maxOccurs="unbounded"`, so
  `PublicationSecondaryIdentifiers(id=[])` fails;
- either/or — `EitherFieldMixin` stands in for an `xs:choice`: `Dates` needs
  `invoice` or `paid`, `Data` needs `publication` or `contract`,
  `InstitutionType` needs `name` or `id`;
- exactly-one — `PublicationPrimaryIdentifier` takes a `doi` **or** a
  `bibliographic_information` block, never both or neither, matching an
  `xs:choice` whose members are both required;
- patterns — `Currency` is three uppercase letters and `DateFormat` is
  `YYYY`, `YYYY-MM` or `YYYY-MM-DD`, both spelled as `xs:pattern`; text fields
  built on `NonEmptyString` reject `""` via `xs:minLength`;
- closed content — unknown or misspelled fields are rejected
  (`extra="forbid"`), since the XSD declares no other elements.

### Beyond the schema

openCost constrains dates by pattern only, and a pattern cannot say whether a
day exists. Two checks go further:

- calendar correctness — the shape must also be a real day, so `2020-06-31`
  fails even though the upstream XSD pattern accepts it; an impossible `to`
  date did reach the upstream example documents (opencost-de/opencost#109);
- ordered date ranges — `participation` and `invoices_period` reject a `from`
  that is clearly after `to`. Each value counts as the year/month/day span it
  covers, so mixed precision (`from="2024"`, `to="2024-12"`) stays valid.

Precision itself is left alone: `2024-12` is never expanded into a full date.
Everything else the models reject is also rejected by the XSD.

Documents that are schema-valid but calendar-invalid therefore no longer parse;
`from_xml` reports the element path, e.g.
`contract.0.participation.to`.

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

