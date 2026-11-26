# Changelog

This file documents all notable changes to this project.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Minor releases in the 0.x series can contain breaking changes. Each release
lists them under **Breaking changes**.

Bullets marked `Upstream:` come from the openCost schema or its example
documents. Bullets marked `Package:` come from this library.

## [0.4.0] - 2026-11-26

This release supports newer upstream openCost schema elements. It also adds
JSON Schema output.

### Added

- Upstream: `PublicationPrimaryIdentifier.id` accepts a primary identifier
  with a scheme and a value. New types: `PublicationPrimaryIdType` and
  `PublicationPrimaryIdTypeEnum`. The schemes are `doi`, `handle`, `urn`,
  `isbn`, `arxiv` and `ark`.
- Upstream: `PublicationType.host_item` and `PublicationHostItemType`
  describe the bibliographic host item, such as the book of a book chapter.
  A host item has one or more primary identifiers.
- Upstream: `PublicationSecondaryIdTypeEnum` accepts the `ark` and `purl`
  schemes.
- Package: dates must be real calendar dates. Dates that pass the XSD
  pattern but name a missing day, such as `2020-06-31`, now fail validation.
- Package: `participation` and `invoices_period` reject a `from` range that
  starts after the `to` range ends. Mixed precision, such as `from="2024"`
  and `to="2024-12"`, stays valid.
- Package: `examples/opencost.schema.json` contains a JSON Schema for
  openCost JSON records. The schema wraps each record in a top-level `data`
  property.
- Package: `examples/json/` contains JSON versions of the upstream XML
  examples.

### Changed

- Upstream: `PublicationPrimaryIdentifier` requires exactly one of `doi`,
  `id` or `bibliographic_information`. The JSON Schema uses `oneOf` for this
  rule.
- Upstream: `BibliographicInformation.isPartOf` is optional, as the XSD
  specifies with `minOccurs="0"`.
- Package: the JSON Schema rejects records that break an either/or or
  exactly-one rule.
- Package: other identifier and structure changes are additive. Documents
  that `0.3.0` accepted still parse, except for the date checks below.

### Deprecated

- Upstream: `PublicationPrimaryIdentifier.doi` remains for compatibility.
  Use the `id` block instead.

### Fixed

- None.

### Breaking changes

- Upstream: `BibliographicInformation.isPartOf` is now `str | None`. Code
  that assumed the field is always present must handle `None`.
- Package: `model_dump()` without `exclude_none=True` now emits null keys
  for optional fields: `id` on `PublicationPrimaryIdentifier`, `host_item`
  on `PublicationType`, and `isPartOf` on `BibliographicInformation`. Exact
  dict comparisons change. Output with `exclude_none=True` does not change.
- Upstream: new enum members can break exhaustive `match` statements.
- Package: documents with an invalid calendar date or an inverted date range
  now fail. Earlier versions accepted these documents.

## [0.3.0] - 2026-09-17

### Added

- None.

### Changed

- Upstream: the models use a newer upstream schema. Apart from the Ringgold
  fix below, XML output does not change.

### Fixed

- Upstream: corrected the Ringgold identifier spelling from `ringold` to
  `ringgold` in the model, the enum value and the XML output.

### Breaking changes

- Upstream: `InstitutionIdType.ringold` is now `InstitutionIdType.ringgold`.
  Code that uses the old member fails.
- Upstream: XML documents with `<type>ringold</type>` no longer parse. Use
  `<type>ringgold</type>`.

## [0.2.0] - 2026-09-11

### Added

- Upstream: contracts accept `opencostid` as a primary identifier scheme.
- Upstream: contract secondary identifiers accept the `ESAC` and
  `opencostid` schemes.
- Upstream: `CoarPublicationType` now has 306 values. It covers the v3.2
  English labels and their `https` and `http` PURLs. All earlier values
  remain.

### Changed

- None.

### Fixed

- None.

### Breaking changes

- Upstream: no breaking change for existing documents. New enum members
  can break exhaustive `match` statements.

## [0.1.1] - 2026-09-09

### Added

- Package: the package ships `py.typed`, so type checkers use its inline
  annotations (PEP 561).

### Changed

- None.

### Fixed

- None.

### Breaking changes

- None.

## [0.1.0] - 2026-09-09

Initial package release. All entries below are package features, built on
the upstream openCost schema.

### Added

- Pydantic models for the openCost schema: `data`, `publication`, `contract`
  and their identifier, institution, invoice and cost-data types.
- Field descriptions and docstrings from the upstream openCost
  documentation, with § section references.
- `to_xml` and `from_xml` work from the models. Aliases become element
  names, enums use their schema values, the serializer omits `None` fields,
  and round-trips are lossless.
- Strict model validation: unknown fields fail, required lists need at least
  one item, and `EitherFieldMixin` enforces at-least-one choices.
- Tests check generated XML and the upstream example files against the
  official openCost XSD.
- The package uses the GPL-3.0-or-later license.

### Changed

- None.

### Fixed

- None.

### Breaking changes

- Initial release.

[0.4.0]: https://github.com/coda-oa/opencost-py/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/coda-oa/opencost-py/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/coda-oa/opencost-py/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/coda-oa/opencost-py/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/coda-oa/opencost-py/releases/tag/v0.1.0
