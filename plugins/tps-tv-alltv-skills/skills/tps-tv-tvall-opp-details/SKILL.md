---
name: tps-tv-tvall-opp-details
description: Adapts get-tps-central-context from the required cxl-workbench-alltv plugin into pre-request opportunity context, enriched with TPSC project data. Use for an opportunity URL/reference, account-plus-owner lookup, manual pre-request context, or a known project's status/widget. Full context uses the provider; known-ID status/widget delivery remains valid even when requests exist and uses TPSC plus mandatory Workfront freshness checks. An issue input goes to tps-tv-tvall-request-details; a person's pipeline goes to tps-tv-tvall-my-opp-summary.
metadata:
  version: "2.0.0"
  visibility: public
---

# TPS TV/AllTV Opportunity Details

## Responsibility and prerequisites

This is the opportunity adapter over `get-tps-central-context` from required
`cxl-workbench-alltv` 1.1.0 or later, not a second deep Workfront gather.
Read `reference/context-provider.md` for loading the provider, native IDs,
schema 2.1, reuse rules, and common-layer mappings. Missing installation is an
explicit dependency error, not a reason to restore the removed gather.

The provider owns anchor resolution and all deep Workfront context.
This skill shapes the opportunity output and handles TPSC enrichment, related
display eligibility, narrow freshness checks, and presentation. TPSC read tools
fetch data only; widget tools display the supplied `data` and do not fetch.

The full gather is pre-request. Classification belongs to the provider.
The known-ID fast path is independent: run it even if a request exists, a
request-details skill ran earlier, or the session discussed that request.
No portfolio gather or upload here; route pipeline asks to
`tps-tv-tvall-my-opp-summary`, and uploads to the request/upload adapters.

## Workflow

### Step 0: Choose presentation and route

Resolve `useWidget` from explicit session preference, then prior interaction,
otherwise false; never block on a preference question.

If `tpsprojectid` and `tpsaccountid` are known and the ask is status/widget only,
use Step 0b. Otherwise use Step 1 for full context or anchor resolution.

### Step 0b: Known-ID status/widget fast path

1. Silently call `tps_tv_read_tpsc_opp_detail` with the known IDs. It returns
   `{ projects, accounts }`, with `requests[]` nested on each project.
2. Apply Step 3's related-project eligibility filter. Never gate the anchor
   itself on whether a request exists.
3. Read and execute `reference/same-day-refresh.md` for every surviving
   project (`tpsprojectid`) and every nested request (`tpsrequestid`).
   Preserve nesting; no one-hour record cache and no new-record discovery.
4. Pass the corrected payload as `data` to
   `tps_tv_read_tpsc_opp_detail_widget` only when `useWidget` is true;
   otherwise present in text. Include freshness counts/failures.
   No full gather or context file on this path.

### Step 1: Obtain the main Workfront context

Invoke the installed provider as described in `reference/context-provider.md`.
Pass `workfront_opportunity_url`, `workfront_opportunity_reference`,
`account_name`/`owner_name`, or `manual_context`, with
`context_scope: anchor_only` and `presentation: return_to_caller`.
For a known project GUID on a full-context ask, pass `workfront_opportunity_id`.
If the other adapter already passed a provider result for this same anchor
during this invocation, validate and consume it rather than invoking again.
Do not perform an independent Workfront lookup or extraction first.

If the provider resolves an issue, pass the same-invocation result to
`tps-tv-tvall-request-details`; do not recursively gather it again.
For `needs_input`, surface the provider's recommended next step and stop.
A manual result is an unverified partial, with no invented IDs or TPSC fetch.
An existing request in a TPSC project snapshot does not reclassify a provider
result already anchored on an opportunity project.

On provider read errors, report them and preserve partial context/flags.
If a confirmed project ID exists, a TPSC-only partial answer can still be
produced, explicitly labeled as such. Missing provider installation cannot
be treated as a Workfront outage.

### Step 2: Fetch TPSC opportunity enrichment

Use provider `meta.workfront_ids.project_id` as `tpsprojectid` and confirmed
`program_id` as `tpsaccountid`. Follow the tool's actual input schema; if a
required ID is unavailable, report that blocker rather than substituting a
project ID or sending a placeholder. Validate any returned canonical IDs
against the anchored records.

Silently call `tps_tv_read_tpsc_opp_detail` once. It returns top-level
`projects[]`/`accounts[]`; every project has its own nested `requests[]`.
These requests use `tpsrequestid`, not `tpscrequestid`. Preserve full native
records, activity, and nested requests; empty requests are a valid result.
Report a malformed response, missing matching project, or tool failure rather
than making up empty arrays and claiming success.

### Step 3: Validate related projects and refresh

Only TPSC-returned projects may appear as related projects.
Keep the anchor matched by `tpsprojectid` regardless of requests.
For each other project, confirm a submitted issue with a batched query on its
`drnumber` using the configured issue deal-reference relationship, discovered
at runtime. Do not assume a private field label or relationship path.
Use `reference/same-day-refresh.md` to discover/initialize tools and resolve
paths before building the query. Drop a sibling only when a successful complete
query confirms no issue. Failed/unavailable checks mean unresolved eligibility:
retain those entries with an explicit warning, not a silent deletion.

Execute `reference/same-day-refresh.md` for every surviving project and all its
nested requests on every new ask, before shaping or presentation. Corrections
must land in the source payload, not only in chat. Provider deep reads from the
same invocation may satisfy corresponding confirmed fields, but they do not
replace the native timestamp gate.

### Step 4: Shape the opportunity context

Map common provider layers using `reference/context-provider.md` into
`reference/context-schema.json`. Retain provider `meta`, nulls, provenance,
team enrichment, conflicts, and flags; never refetch missing deep fields.
The provider's anchor-only result has no discovered siblings; keep deep
`linked_opportunities` empty rather than manufacturing sibling context.

- Mirror confirmed IDs at the root and in `tpsc.ids`; request ID is null on
  this opportunity-context path.
- `tpsc.account` is the matching complete TPSC account plus provider
  `account_firmographics.sub_name`.
- `tpsc.project` is the matching entire freshness-corrected TPSC project,
  augmented with provider `objectives`, `use_cases`, and primary-scoped
  `influenced_pipeline_usd`. Do not replace its TPSC-native fields with
  similarly named narrative fields.
- Preserve that project's own `activity` and nested `requests`, including
  any corrections/snapshot added by the mandatory refresh. Never backfill a
  request from its parent project's fields or merge their histories.
- Top-level `tpsc.requests` remains `[]`, distinct from
  `tpsc.project.requests`; `tpsc.sharepoint` remains the not-applicable
  `{"countassets": 0, "assets": []}` for this pre-request adapter.
- Keep fetched/source/note explicit, including provider path, primary-only
  monetary scope, freshness result, and any partial/TPSC-only limitations.

For manual context without IDs, skip TPSC enrichment and GUID checks; report
that no live verification was possible. A TPSC failure does not invalidate
usable provider context, but widgets requiring a matching TPSC project are
not called with fabricated objects.

### Step 5: Validate, write, and present

Verify provider schema 2.1, common-layer mappings, confirmed IDs when available,
the TPSC anchor match, preserved array nesting, and refresh result.
Write `opp-context-<account>.json`, with the account slug lowercased, spaces
hyphenated, punctuation dropped, separately from the provider source file.
Never overwrite the provider's validated context.
Write only in the user's private working environment, never in this public
checkout. Redact source credentials and do not publish tool responses,
customer records, user identities, or uploads.

For `useWidget: true`, call `tps_tv_read_tpsc_opp_detail_widget` with
`data: { projects: [tpsc.project], accounts: [tpsc.account] }`, using corrected
objects. The full-context widget is primary-only, preserving the existing
presentation contract; the fast path can show its surviving related projects.
Keep chat to a short pointer, freshness counts, and important warnings.

Otherwise synthesize the account, headline net-new GNARR with renewal separate,
objectives/use cases, tech-validation context, conflicts, and unverified or
missing data. Do not paste full JSON when the file is available.
No upload, direct-reports lookup, or additional deep gather afterward.

## Resources

- `reference/context-provider.md`: mandatory provider invocation and mapping.
- `reference/same-day-refresh.md`: mandatory refresh on fast and full paths.
- `reference/context-schema.json`: adapted opportunity output shape.
- No private field maps, dictionaries, customer examples, or tenant
  configuration ship here. The provider owns runtime deep-field discovery.
