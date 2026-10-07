---
name: get-tps-central-context
description: Gather authorized Workfront opportunity or request context for Technical Validation. Accept URLs, references, confirmed native GUIDs, scoped account/person lookups, or manual input. Produce a validated structured context with provenance, conflicts, distinct net-new/renewal amounts, and explicit gaps. Acts as the required full-context provider for the TV/AllTV request and opportunity adapters; it does not fetch TPSC widget/history/SharePoint payloads.
metadata:
  version: "2.3.0"
  visibility: public
---

# Get TPS Central Context

Context schema version: **2.1**. Skill version: **2.3**.
All bundled reference data is empty or generalized. Resolve fields and
relationships at runtime through the authorized connector; no private map or
tenant identifier ships with this plugin.

## Inputs and provider controls

Accept `workfront_request_reference`, `workfront_request_url`,
`workfront_request_id`, `workfront_opportunity_reference`,
`workfront_opportunity_url`, `workfront_opportunity_id`, account lookup
(`account_name`, optional `person_name` or `owner_name`), or `manual_context`.
Use this order as precedence when multiple inputs are present; never blend
contradictory anchors. Record contradictions as data-quality flags.

Accept `context_scope` as `family` (default) or `anchor_only`, and
`presentation` as `summary` (default) or `return_to_caller`.
Reject unsupported values explicitly.

`anchor_only` gathers only the anchored issue and its parent project, or the
anchored opportunity project. Do not discover siblings; both linked-opportunity
arrays stay empty, account consistency covers the primary only, and pipeline
rollups are explicitly primary-only. A request's indication of other deals is
not a contradiction merely because the caller excluded siblings intentionally.

`return_to_caller` writes and validates the context normally, then returns its
actual path, classification, and limitations without a separate chat synthesis.
The caller reads that file and owns the final use-case presentation. Ask for
anchor disambiguation when necessary even in this mode.

## Step 1: Discover the authorized connector

Discover and load the connected Workfront tools through the host's supported
tool mechanism. Read usage documentation and list entities in a new session.
Before constructing filters, read the connector's condition/implicit-pattern
documentation, and status/date documentation for those filters.

Use documented single-object summaries if they expose authorized structured
data and sources. Otherwise discover semantic fields and resolve their paths
before querying. Do not pass raw field labels as relation paths, invent API
signatures, use Workfront REST directly, or guess tenant/category/portfolio IDs.
Tenant scope must be supplied privately or resolved through documented lookups.
A missing connector, rejected query, unresolved field, or authorization failure
must be reported explicitly.

## Step 2: Resolve and classify the anchor

For URLs, read the documented object type/GUID from the supplied URL; never
construct a new Workfront URL. For confirmed typed GUIDs, read that exact
object to confirm its type without searching by DR/name. For references,
resolve the native reference field and query the indicated type, trying the
other type only when necessary. A bare reference has no assumed object type.
Prefer a supplied reference over a conflicting URL and flag the disagreement.

For account/person lookups, use resolved fields and authorized tenant scope.
Present matching records for selection; do not auto-select or broaden a
person lookup beyond its documented ownership semantics. Missing or ambiguous
anchors produce `pipeline_stage.status: needs_input` with a recommended next
step. Do not manufacture a request from manual opportunity context.

An issue is post-request; its native parent project is the opportunity anchor.
A project is opportunity/pre-request context. Surface a discovered request
relationship without guessing from an account name or a cached TPSC snapshot.
Preserve a confirmed delivered stage rather than resetting it to post-request.

## Step 3: Gather the context once

Use `reference/context-schema.json` as the output shape. Discover the
configured fields for account firmographics, opportunity details, objectives,
pains, use cases, scope, team, dates, status, risks, and request management.
Keep request objectives separate from the opportunity's business framing.
Read the issue and its parent project, or the anchor project only for a
pre-request input. Batch related reads where supported.

Enrich native user references with authorized email/title in batches and apply
that enrichment consistently. Do not infer missing people from another role.
Retain source attribution, explicit nulls, conflicts, and data-quality flags.
Decode rich text and enum labels using the returned format/metadata, not a
private lookup table. Redact credentials encountered in text or URLs.

Net-new ARR, renewed ARR, and grand total remain distinct. Missing amounts are
unknown, never zero. Discover configured per-solution values; do not invent
lines or split a combined amount by guessing.

For `family` scope only, traverse related projects when documented authorized
relationships identify them; flag unavailable relationships rather than
guessing a private linked-deal field. The optional `tps-project-extractor`
agent can read one resolved object per dispatch; the main skill still performs
cross-object joins, account checks, conflict surfacing, and final assembly.
For `anchor_only`, never dispatch sibling extractors.

Every new invocation reads live records. Prior GUID resolutions/metadata may
be reused, but an earlier record snapshot is not current context.

## Step 4: Stamp and validate the provider contract

Populate `meta.schema_version: "2.1"`, `meta.skill_version: "2.3"`,
`meta.generated_at` in UTC, `meta.context_scope`, and the winning `meta.anchor`.
Anchor types are request/opportunity reference, URL, or ID, `account_lookup`,
or `manual`, as enumerated by the machine schema.

Populate `meta.workfront_ids` from native fields only:
`request_id` from the issue ID or null, `project_id` from the project ID (the
issue's parent project on a post-request path), and `program_id` from that
project's native program relationship. Unavailable IDs remain null and flagged.
Do not put CRM account IDs, DRs, references, or placeholders into this block.

Copy populated common layers into the shape, including nested
`opportunity.opportunity_details`, `opportunity.gnarr`, team, request,
engagement, and scope-appropriate pipeline rollups. Every layer must be
attempted or explicitly unavailable; do not claim an unattempted layer is empty.

Write a candidate file in the private working environment, then run the
bundled `scripts/validate.py <actual-path> context`. Resolve its reachable
plugin path rather than assuming a host path is mounted in the shell.
Do not announce a complete valid context until validation passes; surface
contract errors and partial-read failures separately.

## Step 5: Return the deliverable

The normal deliverable is private `source/context-<account-slug>.json`.
Never commit generated context, account data, user identities, tool responses,
credentials, or uploads into this public checkout. Do not overwrite an adapted
TV/AllTV file containing `tpsc`; use a separate provider path and return it.

With `return_to_caller`, return the validated file path, classification,
conflict/gap counts, and any recommended next step. Otherwise summarize the
account, scope, headline net-new amount with renewal separate, goals, risks,
and unresolved data. TPSC tools and widgets are not called by this provider.

## Resources

- `reference/context-schema.json`: empty field-by-field context shape.
- `${CLAUDE_PLUGIN_ROOT}/schemas/context.schema.json`: formal machine contract.
- `${CLAUDE_PLUGIN_ROOT}/scripts/validate.py`: standard-library validator.
- `${CLAUDE_PLUGIN_ROOT}/agents/tps-project-extractor.md`: optional object reader.
