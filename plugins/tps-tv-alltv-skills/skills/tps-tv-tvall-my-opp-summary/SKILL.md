---
name: tps-tv-tvall-my-opp-summary
description: Summarize the signed-in user's or a named colleague's TV/AllTV pipeline through tps_tv_read_tpsc_user_summary, then perform mandatory batched native Workfront timestamp checks and same-day field refresh before text or widget output. Never present the TPSC snapshot as refreshed without actual Workfront reads. At the start of a conversation with no presentation preference, briefly offer interactive widgets or conversational text and ask once. Preserve that useWidget boolean on all follow-up request/opportunity handoffs. This is a lightweight portfolio roster, not a full context gather per row.
metadata:
  version: "1.2.0"
  visibility: public
---

# Technical Validation Pipeline Summary

## Non-negotiable execution order

**Resolve preference -> fetch TPSC -> actually check native Workfront timestamps
-> refresh today's records -> verify refresh evidence -> present corrected data.**

The TPSC read is a snapshot, not the end of this workflow. The summary is not
ready after `tps_tv_read_tpsc_user_summary` returns. Reading refresh instructions,
planning a query, a TPSC timestamp, or a check from an earlier ask is not
evidence that this ask's Workfront checks ran. "Lightweight roster" prohibits
per-row full gathers, not the required batched freshness reads.

## Step 0: Resolve presentation, with one-time onboarding

Read and execute `reference/widget-preference.md` before any data call.
When this summary starts the conversation block with no known preference,
briefly offer interactive widgets or conversational text, ask once, and wait.
Record the answer as `presentationPreference.useWidget` and retain the original
pipeline target for resumption. An explicit preference in the original ask skips
the question. Do not re-ask or reset the boolean on subsequent summary/details.

## Step 1: Fetch the authorized TPSC roster (silent)

For "my" pipeline with no person named, call `tps_tv_read_tpsc_user_summary`
according to its documented current-user default. For a named colleague, pass
the supplied name/email according to its advertised schema. Do not guess IDs
or spelling, call `tps_tv_read_direct_reports`, or do a separate team/person
enumeration. Report an ambiguous/rejected target or authorization error.

Inspect the advertised response shape and preserve all native records/fields.
For the documented summary shape, use every top-level `requests[]` entry's
`tpscrequestid` (with the c) as its Workfront issue GUID, and every `projects[]`
entry's `tpsprojectid` as its Workfront project GUID, independently of request
matches. Do not use detail tools' `tpsrequestid` here unless the actual schema
documents that field. A malformed response or missing GUID is not an empty
success. Do not discover additional records by DR/name.

## Step 2: Mandatory native timestamp calls (silent)

Read `reference/same-day-refresh.md` for connector initialization, date handling,
confirmed semantic mappings, and explicit failure behavior. Execute this step
inline on every new summary ask; do not stop at loading the reference.

1. Collect distinct valid issue/project GUIDs. Keep missing-GUID entries in
   scope and mark them unresolved. An empty collection needs no query; a
   nonempty response with missing IDs cannot count as successfully checked.
2. Discover/load the Workfront insights tools even if they were not initially
   visible. A hidden tool is not an unavailable connector. For a new session,
   initialize usage/entity documentation and filter documentation as required.
3. Use field discovery and `insights_get_field_paths` to resolve each root's
   own native ID and `lastUpdateDate`. Do this before custom refresh-field
   discovery; ambiguity in a status mapping must not prevent timestamp checks.
4. **Call `insights_find_workfront_data`** for each nonempty entity collection:
   - issue-rooted, native ID `in` collected `tpscrequestid` values;
   - project-rooted, native ID `in` collected `tpsprojectid` values.
   Request native ID **and** `lastUpdateDate`, map rows by GUID, and exhaust
   pagination/documented batch limits. Use resolved paths, not guessed API paths.
5. Compare native timestamps to today in the session's explicit timezone,
   otherwise UTC. Queue today's GUIDs for Step 3. Earlier valid dates are
   checked-not-today, not proof that all older TPSC data synchronized. Missing,
   malformed, future, or unmatched timestamps are unresolved, never unchanged.

Maintain a logical per-GUID `freshnessEvidence` ledger for this invocation:
`pending`, `checked-not-today`, `updated-today`, `refreshed`, `partial`, or
`check-failed`. Assign checked states only from actual returned Workfront rows.
Record connector/field/query failures explicitly; never invent successful counts.
This ledger is internal bookkeeping, not a new MCP parameter or a public file.

No previous-ask record cache is allowed. A repeated summary minutes later
requires the timestamp calls again. Programs are not refresh targets.

## Step 3: Refresh records changed today (silent)

For today's queued GUIDs, discover and confirm the configured mappings for:
request stage -> `requeststage`, request health -> `requesthealth`, blockers
-> `blockerinfo`, latest update/comment -> `latestcomment`; project technical
case completion -> `techcasestatus`, mitigation comments -> `techriskcomments`.
Resolve paths using the live connector. If a mapping cannot be confirmed,
retain that snapshot field and explicitly mark a partial refresh; do not skip
the other confirmed fields or retroactively discard the timestamp check.

Batch live issue/project reads by GUID, with native IDs in each result.
Apply returned values to the existing TPSC objects, decoding rich text/enums
and clearing stale values to null only for successfully returned empty fields.
Missing/failed fields remain flagged, not fabricated. Preserve unrelated values,
array membership, and historical activity as the shared procedure specifies.
Do not re-call TPSC or run a full context provider per row to simulate freshness.

Update the evidence ledger from these actual read results. No `updated-today`
entry may be presented without a `refreshed` or explicit `partial`/failed outcome.

## Step 4: Completion gate, then presentation

Before any pipeline synthesis or widget call:
- Every in-scope GUID has a timestamp result or an explicit failure.
- No entry remains `pending`; every `updated-today` entry has live corrections
  or a reported partial failure.
- Corrections are on the exact objects to be presented, not only mentioned in
  chat, and checked/refreshed counts are supported by actual tool results.
- Recover `presentationPreference.useWidget` using the shared preference
  procedure; never infer false from this tool's data-only response.

If timestamp checks or refresh reads failed, retain usable data only as an
explicitly **unrefreshed/partially refreshed TPSC snapshot**, with the actual
connector/mapping error. Do not label that result "current" or report invented
check counts. A successful empty roster may say that there were no records to
check. This gate is mandatory for both presentation styles.

For true, call advertised `tps_tv_read_tpsc_user_summary_widget` separately with
`data: { projects, requests }`, the corrected native arrays. The data read is
not a widget display. Missing presentation tools must be reported, never silently
reinterpreted as a text preference. For false, summarize the corrected roster in
text. Either way, briefly report actual requests/projects checked/refreshed and
limitations. Keep net-new/renewal separate and avoid duplicate project totals.

## Follow-up handoff

An anchored full-context follow-up goes to `tps-tv-tvall-request-details` for
a confirmed issue, or `tps-tv-tvall-opp-details` for a project-only opportunity. Pass original
URLs/references or confirmed IDs **and `presentationPreference`**, not an
ambiguous account name or a fresh default boolean. Those adapters use
`get-tps-central-context` from required `cxl-workbench-alltv` 1.1.0 or later.
Do not invoke that provider for every summary row.

## Data handling and resources

Use only authorized records. Never commit roster responses, user identities,
customer details, credentials, or generated reports to this public repository.

- `reference/widget-preference.md`: required preference resolution and handoff.
- `reference/same-day-refresh.md`: required shared refresh details; the inline
  timestamp-call and completion gates above must also be executed.
