# Workfront context provider contract

This procedure is shared by both detail adapters. Identical local copies keep
each skill self-contained; keep the copies synchronized.

## Load and invoke

Full context requires installed `cxl-workbench-alltv` 1.1.0 or later and its
`get-tps-central-context` skill. Resolve that plugin through the host's installed
skill discovery, then load/invoke the skill using the host's supported mechanism.
Do not guess an MCP tool name, use another plugin's files relative to this
plugin root, or implement a fallback deep gather. If unavailable, explicitly
request installation/enabling of the provider plugin and stop the full gather.
Known-ID detail status paths do not require a full gather. Portfolio summaries
never invoke this provider or Workfront; their data comes only from the TPSC
summary tool. Only a separate user-requested detail ask may enter this contract.

## Read profiles

CXL 1.2.0 adds `context_profile: full` (default) and `widget_enrichment`.
Full-context/artifact requests retain `full`. Known-ID status/widget reads
still bypass the provider. Widget/status reads needing anchor resolution or
explicit Workfront enrichment use `widget_enrichment` with `anchor_only`.
Selection is based on the requested content, never on `useWidget` alone.
Unsupported reduced profiles are a dependency error, not a broad-read fallback.

Reduced results preserve schema 2.1 but declare their profile and excluded
layers. Require `meta.context_profile: widget_enrichment` and an explicit
`meta.enrichment_fields` array for reduced calls. Reject mismatched profiles;
never reuse reduced results for full-context/artifact requests. A full result
may satisfy a reduced ask in this same invocation, without another gather.
Legacy results without a profile count as `full` only.

Pass the user's original URL/reference/account lookup. For confirmed GUIDs,
use provider `workfront_request_id` or `workfront_opportunity_id`, not a made-up
URL. Alternatively pass an already-confirmed
provider result from this same invocation. Set `context_scope: anchor_only` and
`presentation: return_to_caller`. The provider resolves/disambiguates the anchor,
gathers and enriches its context, validates it, and writes its source file.
Read its actual returned file path (or consume a populated same-invocation result); never assume
the path or account slug. Only reuse a result for the same anchor during this
invocation (including an adapter handoff). On a later user ask, gather again for
full context; old files are not proof of freshness.

Require `meta.schema_version == "2.1"` and `meta.context_scope == "anchor_only"`.
An incompatible result is an explicit contract error, not a missing-field
fallback. Preserve `meta.generated_at` and `meta.anchor`, and retain provider
errors, conflicts, sources, and `data_quality_flags`.

## Native IDs and routing

Read `reference/native-id-dictionary.md`: `tpsrequestid = issue.id`,
`tpsprojectid = project.id`, and `tpsaccountid = program.id`.
These mappings are fixed; resolve connector syntax only when not already known.

- `meta.workfront_ids.request_id` is the native Workfront issue GUID or null.
- `meta.workfront_ids.project_id` is the native opportunity project GUID.
- `meta.workfront_ids.program_id` is that project's native program GUID or null.

Never substitute `account_firmographics.account_id`, SFDC IDs, DR numbers, or
references for these GUIDs. Never fabricate a Workfront URL. Existing provider
`record_links` are copied, not reconstructed. Missing required native IDs are
flagged and block the corresponding TPSC call.

An issue/post-request/delivered result belongs to request-details; a project/
pre-request result belongs to opportunity-details. Use `meta.anchor` and the
confirmed IDs, not the mere presence of TPSC requests or the input parameter's
name, to classify. `needs_input` returns the provider's recommended next step.
An adapter handoff passes the result and ends the original adapter; do not loop
back or invoke the provider twice. Manual context is unverified and cannot
manufacture a request for the post-request adapter.

## Common-layer mapping

Start with the local adapter output shape. Copy these provider keys without
reinterpreting their values:

`account`, `record_links`, `account_firmographics`, `opportunity`, `offering`,
`products_in_scope`, `timeline`, `team`, `objectives`, `use_cases`, `request`,
`engagement`, `narrative_context`, `influenced_pipeline_usd`, `conflicts`,
`data_quality_flags`, `pipeline_stage`, and `meta`.

`opportunity.opportunity_details` is **nested**, not a top-level provider key.
GNARR is `opportunity.gnarr`, with net-new, renewed ARR, and grand total separate.
People are already enriched objects; do not re-resolve users. Preserve request
objectives separately from the opportunity's business objectives/use cases.
Unavailable fields remain null/empty per the shape, with gap flags rather than
new deep reads. Keep the provider's request-stage classification, including
`delivered`; never reset it to `post_request`.

Do not import a provider's linked family into an adapter's TPSC display.
`anchor_only` deliberately excludes deep sibling discovery. Related candidates
come only from the adapter's TPSC response; their eligibility and shallow shape
remain the adapter's responsibility. An anchor-only rollup covers the primary
project, not a verified family total.

## Enrichment and output

The provider does **not** return `tpsc` data. The adapter separately calls its
existing TPSC read tool for history, TPSC-native fields, and SharePoint metadata.
Preserve complete returned records, including fields not enumerated in an
example shape. Then run the local mandatory same-day refresh before presenting.
Do not assume a narrative field has the same Workfront mapping as a refresh
field: in particular provider `engagement.latest_update` and TPSC
`latestcomment` may refer to different fields. Reuse a same-invocation live
field only when its exact source matches the confirmed refresh mapping.

The adapted file is a different deliverable from the provider source file.
If a legacy provider run wrote its file flat at the adapter's intended
`context-<account>.json` path, put the adapter file in a separate `tvall/`
directory and return that actual path. Never overwrite the provider file.
Do not validate the enriched adapter against the provider schema as though
the two contracts were interchangeable.

The raw provider context is never a valid upload payload or widget payload.
Request-details builds `tpsc.requests` and lifts SharePoint metadata;
opportunity-details preserves each project's nested `requests[]`.
Only the adapters assemble those use-case-specific outputs.

Use `reference/widget-mapping.md` for exact provider-to-native enrichment,
including deterministic helper execution and selected-field/null precedence.
Preserve complete TPSC records and existing output shapes. Measure mapping
time and file/widget bytes separately from raw Workfront response bytes.
