# CXL Workbench AllTV

This public-safe plugin contains only `get-tps-central-context` and its
dependencies: `tps-project-extractor`, an empty context shape, a JSON Schema
contract, a standard-library Python validator, and synthetic contract tests.
It contains no customer examples, private field dictionaries, tenant IDs,
production endpoints, credentials, or internal Git history.

## Requirements

Install `cxl-workbench-alltv` from the `adobe-dss-aep/tps-tv-alltv-mktplc`
marketplace. Configure an authorized Adobe Workfront MCP separately and make
Python 3 available for validation. The plugin does not bundle an MCP server.
Any tenant configuration must be provided privately by an administrator.

## Provider inputs

The skill accepts request/opportunity URLs, numeric references, confirmed
native GUIDs (`workfront_request_id` or `workfront_opportunity_id`), scoped
account/person lookups, or manual context. Ambiguous anchors require user
clarification.

- `context_scope: family` is the default. It includes related records only
  when the authorized connector returns documented relationships.
- `context_scope: anchor_only` gathers just the issue and its parent project,
  or the opportunity project, without discovering sibling deals.
- `presentation: summary` is the default.
- `presentation: return_to_caller` returns the validated file's actual path,
  classification, and limitations for the calling adapter to consume.
- `context_profile: full` is the default for comprehensive context/artifacts.
- `context_profile: widget_enrichment` requires `anchor_only` and uses the
  explicit field selections in
  [query-profiles.md](skills/get-tps-central-context/reference/query-profiles.md).
  It excludes unneeded deep layers and requires documented connector projection,
  not a broad summary followed by trimming. Excluded layers and failures are
  explicit; this result cannot ground a full-context artifact.

Schema 2.1 includes native Workfront IDs under `meta.workfront_ids` and nests
opportunity details at `opportunity.opportunity_details`. Missing values stay
null with explicit flags; no identifiers or field mappings are invented.
The optional `meta.context_profile` is backward-compatible with existing full
results. Reduced results require selected-path read evidence in
`meta.enrichment_fields` and explicit data-quality limitations.

`tps-tv-alltv-skills` 2.0.0 or later uses this provider for full request/
opportunity context. The adapters separately add TPSC-native history, widgets,
SharePoint metadata, and mandatory per-ask same-day checks. A provider context
alone is not a TPSC widget or upload payload.
TPS 2.4.0 uses CXL 1.2.0 for the reduced profile and deterministic widget
enrichment. TPSC history and existing widget envelopes are not truncated.

## Output and validation

Write generated `source/context-<account>.json` only in the user's **private**
working environment, never in this public checkout. The reference shape is
empty; the machine contract is `schemas/context.schema.json`.

```text
python scripts/validate.py path/to/context-account.json context
```

`context` is also the default schema. Scripts resolve schemas relative to the
plugin root; if `CLAUDE_PLUGIN_ROOT` is set, it must identify a reachable root.

From the marketplace checkout:

```text
python -m unittest discover -s plugins/cxl-workbench-alltv/tests -p "test_*.py"
```

Tests use synthetic values and require the sibling adapter plugin for shape
checks. They do not prove live connector behavior or public-release authorization.
