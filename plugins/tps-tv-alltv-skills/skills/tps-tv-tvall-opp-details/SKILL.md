---
name: tps-tv-tvall-opp-details
description: Gather structured context for an opportunity before a Technical Validation request exists. Use an opportunity URL, verified account/project IDs, an account-and-owner lookup, or clearly labeled manual context. Also support explicit status or widget reads for already-known projects.
metadata:
  version: "1.0.0"
  visibility: public
---

# Technical Validation Opportunity Details

## Prerequisites

Use the authorized Workfront and `tps-tv-alltv-assist` MCP connectors. Follow
the field-discovery and documented query procedure in
`tps-tv-tvall-request-details`: discover entities and fields, resolve paths and
named objects, and read the filter documentation. Never hardcode tenant IDs,
custom-field IDs, portfolio IDs, or relationship paths.

If a connector is missing or a read fails, report it explicitly. Manual context
can produce an unverified partial result; it cannot justify invented identifiers
or a tool call using unverified IDs.

## Full gather

1. Resolve the opportunity from a supplied project URL, reference number, or
   account/owner lookup. Ask for clarification if the anchor is ambiguous.
   Determine whether a validation request exists. If it does, hand off to
   `tps-tv-tvall-request-details`.
2. Once `tpsaccountid` and `tpsprojectid` are verified, call
   `tps_tv_read_tpsc_opp_detail` before deeper Workfront extraction. Respect the
   tool's actual input schema. Its opportunity response contains projects and
   accounts, with requests nested on each project; do not assume a separate
   top-level requests array.
3. Gather the authorized anchor project's firmographics, owners, objectives,
   use cases, value, dates, stage, and risks through discovered Workfront fields.
   Keep net-new ARR, renewed ARR, and grand total distinct. Discover configured
   per-solution fields rather than assuming a fixed private mapping.
4. Do not independently traverse sibling opportunities. Related records are
   limited to records the TPSC tool itself returns.
5. Fill `reference/context-schema.json`, retaining Workfront and TPSC provenance
   separately. Surface conflicts and missing fields; never invent values.
   Mark manual or connector-only context as partial and unverified as applicable.
6. Write `opp-context-<account-slug>.json` outside this public repository. Use
   conversational synthesis unless the user prefers a widget, in which case call
   `tps_tv_read_tpsc_opp_detail_widget` separately with its advertised data input.

## Explicit known-project status or widget read

When the user explicitly asks for status or a widget and already has verified
account/project IDs, call `tps_tv_read_tpsc_opp_detail` directly. This fast path is
not the full pre-request gather: do not refuse it or redirect solely because a
request was discussed earlier.

Keep the requested anchor in scope. Filter any additional returned records to
the user's requested scope and presentation intent; do not discard the anchor
solely because it has an associated request. Report empty results explicitly.
Use `tpsrequestid` for requests from opportunity/detail tools; inspect returned
schemas instead of assuming the user-summary tool uses the same field name.

For returned projects and their nested requests, perform same-day freshness
checks through resolved Workfront update fields. Reuse same-session refreshed
records and refresh only fields returned by Workfront, preserving unrelated
history. Do not repeatedly re-read cached TPSC data as a freshness substitute.
Display a widget only through the dedicated widget tool and only when requested.

## Data handling

Never store credentials found in narratives or links. Do not publish generated
context, account records, user identities, or tool responses to this public repo.
The JSON reference is an empty output-shape template, not a JSON Schema validator.
