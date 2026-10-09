# Workfront query profiles

`context_profile` is `full` by default or `widget_enrichment` when a detail
adapter explicitly requests a reduced read. Profile selection is independent
of widget/text preference. `widget_enrichment` requires `context_scope:
anchor_only`; reject other combinations before querying.

## Query boundary

Use `reference/native-id-dictionary.md` for known native IDs and connector paths.
Do not rediscover which object a TPSC ID identifies or repeat a known ID-path
lookup. Resolve only missing connector syntax and required custom fields.

Resolve the anchor with only native ID/type, reference/name needed for
disambiguation, parent project ID, and program ID. For reduced enrichment,
use explicit field selection through the connector's documented query schema.
Never request wildcard fields, entire custom forms, sharing/access lists,
updates/comments collections, attachments, or user enrichment. Do not use a
single-object summary unless its documented field projection can restrict its
response to the selected meanings. A broad summary followed by local trimming
does not reduce Workfront response size.

If the connector has no documented projection capability, report that reduced
reads are unsupported. Do not silently fall back to a broad gather.

## Reduced enrichment field selection

Resolve paths for only these meanings; identifiers and necessary relationships
are always included. No private field names or tenant IDs are assumed.

| Object | Meaning | Provider destination |
| --- | --- | --- |
| project | Account name and SUB name | `account`, `account_firmographics.account_name`, `account_firmographics.sub_name` |
| project | Confirmed native object link | `record_links.primary_opportunity_project` |
| project | Separate net-new, renewal, combined monetary values | `opportunity.gnarr.net_new_usd`, `opportunity.gnarr.renewed_arr_usd`, `opportunity.gnarr.deal_grand_total_usd` |
| project, opportunity anchor only | Business objectives and use cases | `objectives`, `use_cases` |
| issue, request anchor only | Confirmed native issue link | `record_links.tv_request_issue` |
| issue, request anchor only | Request objectives, use cases, products, proposed dates/flexibility | `objectives`, `use_cases`, `products_in_scope`, `timeline` |

Read ID and native `lastUpdateDate` alongside selected fields so same-invocation
refresh can reuse those results when their exact sources match. Request
management/technical-risk refresh remains the adapter's separate narrow phase.
Never substitute narrative engagement fields for those refresh mappings.

Batch selected fields for each root where supported. Exhaust documented pages
and respect query limits; do not sample or truncate text, arrays, or records.
Do not fetch excluded fields to fill the full template's empty placeholders.

## Contract and completeness

Keep schema 2.1 and the existing output shape. Stamp `meta.context_profile`.
For reduced results, set `meta.enrichment_fields` to the provider paths actually
retrieved for adapter enrichment, including confirmed empty values:
`account_firmographics.sub_name`, `record_links.primary_opportunity_project`,
`record_links.tv_request_issue`, `objectives`, `use_cases`, `products_in_scope`,
`timeline`, and `influenced_pipeline_usd`, as applicable. Missing/failed paths
are excluded and flagged; template placeholders are not read evidence.

Derive `influenced_pipeline_usd` only from the selected primary project's
confirmed monetary values, preserving unknowns and separate net-new/renewal.
Mark it primary-only. If any monetary read fails, flag the gap; do not fabricate
a family rollup.

Add an explicit data-quality flag that this is reduced widget enrichment, not
complete artifact-grounding context. Retain excluded layers as null/empty
template values and identify the deliberately excluded layer groups in flags.
The full profile retains the comprehensive gather and completeness gate.

## Measurements

When observable, record Workfront call count and UTF-8 serialized response
bytes separately from provider file bytes. Do not call an estimate measured
bytes or infer raw response size from a trimmed fragment. Report unavailable
metrics as unavailable. No performance target is claimed without a live trace.
