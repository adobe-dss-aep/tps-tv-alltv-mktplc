---
name: tps-tv-tvall-request-details
description: Adapts get-tps-central-context from the required cxl-workbench-alltv plugin into post-request TV/AllTV engagement context, enriched with TPSC history and SharePoint metadata. Use for an existing TV request URL/reference, a DR/account with a submitted request, full context before TV artifacts, or context needed for a SharePoint attachment. Known-ID status/widget asks use a lightweight TPSC read and mandatory Workfront freshness checks instead of a full gather. An opportunity-only input goes to tps-tv-tvall-opp-details; a person's pipeline goes to tps-tv-tvall-my-opp-summary.
metadata:
  version: "2.1.2"
  visibility: public
---

# TPS TV/AllTV Request Details

## Responsibility and prerequisites

This skill is a **post-request adapter**, not an independent Workfront context
gatherer. `cxl-workbench-alltv` 1.1.0 or later must be installed for full context.
Load its `get-tps-central-context` skill using the host's skill mechanism.
Do not treat a skill name as an MCP tool or read another plugin through this
plugin's `${CLAUDE_PLUGIN_ROOT}`. If the provider cannot be loaded, report that
dependency and request installation; do not substitute the removed full gather.

The provider owns anchor resolution, issue/project extraction, firmographics,
GNARR, team enrichment, provenance, narrative, conflicts, and validation.
This skill owns TPSC reads, sibling display eligibility, mandatory same-day
refresh, adapter shaping, widget presentation, and SharePoint metadata.
Only narrow ID resolution, sibling validation, and freshness reads are made
directly through Workfront here; never duplicate the provider's deep gather.
Read `reference/context-provider.md` for the provider contract and mappings.

TPSC tools are separate from the Workfront MCP. Read tools fetch data only;
`tps_tv_read_tpsc_request_detail_widget` only displays its `data` argument.
Uploads are a separate, explicit intent handled by
`tps-tv-tvall-add-to-sharepoint`, never an automatic action after gathering.

## Workflow

### Step 0: Route the ask and choose presentation

Read `reference/native-id-dictionary.md` before Workfront queries, including
fast paths. TPSC IDs already equal native issue/project/program IDs. Use known
connector ID paths directly; do not search for custom TPSC ID fields.

Read and execute `reference/widget-preference.md` **before routing**. Recover
the conversation's `presentationPreference.useWidget`, including an explicit
false. A follow-up inherits the resolved boolean; do not ask again or default
true back to false. Pass `presentationPreference` on any logical skill handoff.

- A person's open requests/pipeline with no specific deal: hand off to
  `tps-tv-tvall-my-opp-summary`. Team-roster questions are out of scope; never
  call `tps_tv_read_direct_reports`.
- Known `tpsrequestid`, `tpsprojectid`, and `tpsaccountid`, status/widget only:
  use Step 0b unless extra Workfront enrichment was explicitly requested.
  This does not produce full context or ground a TV artifact.
- All other anchored full-context asks: use Step 1. Accept a
  `workfront_request_url`, `workfront_request_reference`, or `account_name`
  with optional `person_name`; person-only lookup is also passed to the provider.
  Preserve reference-over-URL precedence and provider disambiguation.
- An opportunity input with no request goes to `tps-tv-tvall-opp-details`.

For widget/status asks without confirmed IDs, or an explicit request to enrich
a widget with Workfront objectives/scope, use Step 1 with
`context_profile: widget_enrichment`, then the existing TPSC/filter/refresh
steps. Full-context/artifact asks use `context_profile: full`, even if delivered
in a widget. Known-ID status asks keep Step 0b with no provider gather.
`useWidget` alone never selects the reduced profile. Reduced output must be
labeled widget enrichment, not complete context for an artifact.

Resolve a default only when no earlier choice/state exists, as the shared
procedure specifies. Provider `presentation: return_to_caller` is independent
of `useWidget`; do not reinterpret it as conversational preference.

### Step 0b: Known-ID status/widget fast path

1. Call `tps_tv_read_tpsc_request_detail` with the known IDs, silently.
2. Apply Step 3's sibling filter to the returned projects.
3. Read and execute `reference/same-day-refresh.md` on every remaining project
   and every returned request. Request GUIDs are `tpsrequestid`, not the
   summary tool's `tpscrequestid`. No previous-ask record cache is allowed.
4. For `useWidget: true`, pass the corrected native payload to
   `tps_tv_read_tpsc_request_detail_widget` as `data`. Otherwise present it
   in text. Include checked/refreshed counts and any failure. No file or full
   gather on this path.
   Immediately before output, reread `reference/widget-preference.md` and
   verify the latest resolved boolean. Report a failed widget as a presentation
   limitation, never silently change the preference.

### Step 1: Obtain the main Workfront context

Read and execute `reference/context-provider.md`. Invoke
`get-tps-central-context` with the original anchor inputs,
`context_scope: anchor_only`, and `presentation: return_to_caller`.
Pass the profile selected in Step 0. Reduced reads require CXL 1.2.0 or later;
if unsupported, report the version dependency instead of running a broad gather.
For a known issue GUID on a full-context ask, pass `workfront_request_id`.
If the other adapter already passed a provider result for this same anchor
during this invocation, validate and consume it rather than invoking again.
Do not independently search Workfront first or regenerate already-returned
context layers. Use the provider's same-invocation result as the base.

- `needs_input`: surface the provider's recommended next step; stop.
- A resolved project without a request: pass the provider result to
  `tps-tv-tvall-opp-details` with `presentationPreference`, without recursively
  gathering again.
- A resolved issue, including a delivered request: continue.
- Provider error/partial result: report it and retain flags. If confirmed
  request/project IDs are available, a TPSC-only partial answer is allowed;
  never label it complete Workfront context. Without IDs, stop and request
  the missing anchor. A missing provider installation is not an outage fallback.

### Step 2: Fetch TPSC enrichment

Take `tpsrequestid` and `tpsprojectid` from `meta.workfront_ids`.
Use its confirmed `program_id` for `tpsaccountid` when available. The tool's
current schema determines which IDs are required. If a required account ID
is unavailable, report that blocker; do not substitute a project ID as a
placeholder. Use only verified native IDs and validate any canonical IDs
returned by the connector against the anchored records.

Call `tps_tv_read_tpsc_request_detail` once with those arguments, silently.
Preserve its full account/project/request records, history, and SharePoint
metadata. Normalize only a documented response envelope: request details
may carry the arrays under `data`; do not invent absent arrays or silently
treat a malformed response as no records. Report errors or no matching anchor.
Do not replace TPSC history or SharePoint data with the provider's narrative.
If enrichment fails, retain usable provider context and explicitly set
`tpsc.fetched: false`. Do not render a TPSC widget or start an upload with
fabricated account/project/request objects.

### Step 3: Filter sibling projects and refresh the TPSC snapshot

The primary project is matched by `tpsprojectid`, never by response order.
Only projects already returned by TPSC are candidates for related projects.
For other projects, confirm a submitted issue by their `drnumber` using a
batched issue-rooted filter on the configured deal-reference relationship,
discovered at runtime. Do not assume a private field label or relationship path.
Initialize/discover the insights connector and resolve paths as specified in
`reference/same-day-refresh.md` before querying. Keep the anchor regardless.
Drop a sibling only after a successful, complete query confirms no issue;
an unavailable/failed check is unresolved eligibility, not proof of absence.
Retain unresolved candidates with a warning rather than silently deleting them.
Never discover additional projects through a Workfront DR list.

Read and execute `reference/same-day-refresh.md` for every surviving project
and every returned request before assembly or presentation. Today's confirmed
fields must overwrite the TPSC source objects. A provider context is not a
replacement for native timestamp checks; only live reads from this same
invocation may satisfy individual refresh fields.

### Step 4: Shape the request context

Use `reference/context-schema.json` as the adapter shape and the mapping in
`reference/context-provider.md`. Copy common context layers from the provider;
preserve nulls, sources, conflicts, team enrichment, and flags. Missing provider
fields stay null/empty as the shape requires, with an explicit gap flag.
Preserve `meta.context_profile` and `meta.enrichment_fields`. For reduced
results, excluded layers are intentionally not gathered, never complete
artifact-grounding context.
Do not refetch deep fields to fill them. Keep the provider's `meta` block.
Store the resolved `presentationPreference` in the adapted file, separately
from the provider metadata and TPSC widget payload. Missing provider `useWidget`
does not erase that setting.

Read and execute `reference/widget-mapping.md` for provider-to-native enrichment.
Use its helper on the selected, freshness-corrected widget envelope when Python
is available; otherwise explicitly report manual mapping and apply its table.
Only confirmed selected enrichment may overwrite TPSC values. Unselected
template nulls/empties never erase native fields. The helper preserves unrelated
fields/history; retain this step's request selection and SharePoint lifting.

- Set root ID mirrors and `tpsc.ids` from confirmed IDs, not placeholders.
- `tpsc.account`: the matching complete TPSC account, plus provider
  `account_firmographics.sub_name`.
- `tpsc.project`: the matching complete, freshness-corrected TPSC project,
  plus `primary_opportunity_link` from provider `record_links`,
  request-level `objectives`, `use_cases`, and the scoped
  `influenced_pipeline_usd`. Leave unrelated TPSC-native fields intact.
- `tpsc.requests`: primary request first, matched by `tpsrequestid`, with
  `is_primary: true`, provider `tv_request_link`, `products_in_scope`, and
  `timeline`. Preserve every native field and that request's activity.
  Lift its `sharepoint` object to `tpsc.sharepoint` in the file only.
- Append returned secondary requests whose type is Hands-on Lab (all
  onsite/1:1/virtual variants), Custom Demo, or POC, case-insensitive and
  prefix-tolerant. Set `is_primary: false`; their Workfront-only
  `tv_request_link`, `products_in_scope`, and `timeline` stay null.
  Do not borrow primary fields or history. Bootcamp remains excluded for
  secondary entries, not for the primary request.
- Build `linked_opportunities` from surviving TPSC siblings only, with their
  native IDs/name/DR, `tpsaccountid`, and confirmed issue ID when unambiguous.
  If multiple issues match, do not pick one. This is a shallow related list,
  not a request to gather sibling deep context. Cross-check the provider's
  additional-opportunities signal against it and surface discrepancies.
- The provider's anchor-only GNARR rollup is not a full family rollup.
  Use its primary values; if siblings lack separate confirmed net-new and
  renewal values, flag incomplete family totals and state the primary-only
  scope in `influenced_pipeline_usd.note`. Never split TPSC `totalgnarr` by
  guessing, or present it as verified net-new GNARR.

Keep `tpsc.fetched`, `source`, and `note` explicit, including the provider
file path, refresh result, and any partial/outage status. An unavailable
SharePoint list is unknown: flag it; an empty list is confirmed only when
returned as empty. Do not claim zero assets based on a failed read.

### Step 5: Validate shape, write, and present

Read and execute `reference/widget-preference.md` again after provider/shaping
work and before text/widget output. Recover the user's latest choice rather
than re-defaulting. True requires the request widget; false requires text.
A widget failure is an explicit labeled fallback, not a preference change.

Verify the anchored IDs, provider schema 2.1, attempted context layers, primary
request selection, TPSC enrichment, and refresh result before output.
Do not overwrite the provider's source file. Write the adapted
`context-<account>.json` separately (the existing adapter output location),
with the account slug lowercased, spaces hyphenated, punctuation dropped.
Write only in the user's private working environment, never in this public
checkout. Redact source credentials and do not publish tool responses,
customer records, user identities, or uploads.

For a widget, shape `data` as `{ requests, projects, accounts }`:
`requests` is the adapted `tpsc.requests`, `projects` contains the adapted
primary plus surviving related TPSC projects, and `accounts` retains the
matching TPSC accounts. Reattach `tpsc.sharepoint` to a copy of the primary
request for this widget; keep it lifted in the written context.
Never drop activity, rebuild native records from a partial field list, or send
the unrefreshed response. The widget is the answer; add only a short pointer,
freshness result, and important warnings.

Without a widget, synthesize account, offering, net-new value (renewal
separately), objectives/use cases, relevant status, request count, conflicts,
and unresolved/partial data. Do not dump JSON when the file is available.
For upload follow-ups, pass this adapted context to
`tps-tv-tvall-add-to-sharepoint`; a raw provider context alone is insufficient.

## Resources

- `reference/context-provider.md`: mandatory provider invocation and mapping.
- `reference/widget-mapping.md`: exact enrichment mapping, guards, and helper.
- `reference/widget-preference.md`: mandatory session preference/handoff gate.
- `reference/same-day-refresh.md`: mandatory refresh, fast or full path.
- `reference/context-schema.json`: adapted output shape, not provider input.
- `reference/tpsc-request-details-submission-schema.json`: narrower single
  request submission shape; no activity, `is_primary`, or SharePoint object.
  Keep its copy in the upload skill aligned.
- The local schema is an output template, not an extraction guide. Copy common
  layers from the provider and add the adapter enrichment; do not use template
  fields as instructions for a second deep gather.
- No private field maps, dictionaries, customer examples, or tenant
  configuration ship here. The provider owns runtime deep-field discovery.
