---
name: tps-tv-tvall-my-opp-summary
description: Summarize the signed-in user's or a named colleague's TV/AllTV pipeline through tps_tv_read_tpsc_user_summary, then perform mandatory batched native Workfront timestamp checks and same-day field refresh before text or widget output. Never present the TPSC snapshot as refreshed without actual Workfront reads. At the start of a conversation with no presentation preference, briefly offer interactive widgets or conversational text and ask once. Preserve that useWidget boolean on all follow-up request/opportunity handoffs. This is a lightweight portfolio roster, not a full context gather per row.
metadata:
  version: "1.3.1"
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

Discovering `tps-tv-alltv-assist` tools does not discover the separate Workfront
connector. A tool description that calls widget enrichment "optional" does not
make this skill's refresh optional. A loaded widget is not the next action after
the TPSC read: finish the Workfront phase first.

## Step 0: Resolve presentation, with one-time onboarding

Read and execute `reference/widget-preference.md` before any data call.
When this summary starts the conversation block with no known preference,
briefly offer interactive widgets or conversational text, ask once, and wait.
Record the answer as `presentationPreference.useWidget` and retain the original
pipeline target for resumption. An explicit preference in the original ask skips
the question. Do not re-ask or reset the boolean on subsequent summary/details.

## Step 0a: Discover Workfront before the TPSC read

Read `reference/native-id-dictionary.md`. Summary `tpscrequestid` equals
`issue.id`; `tpsprojectid` equals `project.id`, and `tpsaccountid` equals
`program.id`. Do not search for custom TPSC ID fields.

Use the host's tool-discovery mechanism with a separate Workfront-specific
search, such as `Adobe Workfront insights insights_find_workfront_data`.
Discover/load `insights_read_docs`, `insights_list_entities`,
`insights_search_fields`, `insights_get_field_paths`, and
`insights_find_workfront_data`, including their advertised argument schemas.
Use the exact advertised tool names, including server namespaces when present.
Do not assume the TPSC discovery result contains these tools, or interpret
initially hidden tools as unavailable. Follow discovery pagination/limits when
needed to load the complete required set.

If discovery confirms a required tool is unavailable or reports an error,
retain that actual limitation for the output gate. TPSC may still supply an
explicitly unrefreshed snapshot, never a successfully refreshed summary.

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

Do not synthesize the pipeline or call a widget yet. Continue immediately to
the Workfront timestamp checks below, even if discovery suggested an interactive
tool or the user asked only for a quick summary.

## Step 2: Mandatory native timestamp calls (silent)

Execute the self-contained Workfront phase below on every new summary ask;
do not stop at loading the reference. `reference/same-day-refresh.md` is
supporting documentation, not a delegated execution step.

1. Collect distinct valid issue/project GUIDs. Keep missing-GUID entries in
   scope and mark them unresolved. An empty collection needs no query; a
   nonempty response with missing IDs cannot count as successfully checked.
2. Use the separate Workfront tools discovered in Step 0a. For a new insights
   session, call `insights_read_docs` for `mcp-usage`, then call
   `insights_list_entities`. Read `conditions` and `implicit-patterns` before
   constructing filters, and `dates` before interpreting timestamps.
   Successfully initialized documentation/metadata may be reused in-session.
3. Use known native-ID paths from the dictionary/current session directly,
   including `project.project_ID` for insights projects. Resolve only missing
   issue-ID connector syntax once. Resolve `lastUpdateDate` separately with
   `insights_search_fields`/`insights_get_field_paths` when not already known.
   Roots are `issue` for requests and `project` for projects. Prefer direct
   paths (`backlinks: 0` where supported).
   Use each tool's advertised schema; never invent argument names or paths.
   Do this before custom refresh-field discovery; ambiguity in a status mapping
   must not prevent timestamp checks.
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

**No project-count cutoff:** check every returned project and request, including
large portfolios. Deduplicate IDs, exhaust all pages, and split queries only at
documented connector batch limits. Do not sample, check only the first page,
skip project-only entries, or bypass refresh because of expected latency.
If an actual execution limit interrupts the phase, report the unchecked counts
and the error explicitly; do not turn remaining records into checked results.
This isolated Workfront phase can be removed in a later performance change,
but it is mandatory in this release.

## Step 3: Refresh records changed today (silent)

For today's queued GUIDs, use `insights_search_fields` and
`insights_get_field_paths` to discover and confirm these mappings:

| Workfront root | Meaning to discover | TPSC field to correct |
| --- | --- | --- |
| issue | Request management stage | `requeststage` |
| issue | Request management health | `requesthealth` |
| issue | Request blocker information | `blockerinfo` |
| issue | Request latest update/comment | `latestcomment` |
| project | Technical-case completion status | `techcasestatus` |
| project | Technical-risk mitigation comments | `techriskcomments` |

Resolve paths using the live connector; no private field names/IDs are assumed.
If a mapping cannot be confirmed,
retain that snapshot field and explicitly mark a partial refresh; do not skip
the other confirmed fields or retroactively discard the timestamp check.

**Call `insights_find_workfront_data` again** for each nonempty group changed
today: an issue-rooted query and a project-rooted query, filtered by that root's
native ID `in` today's queued GUIDs. Request native ID, `lastUpdateDate`, and
every confirmed refresh-field path. Batch and paginate using documented limits.
No field-read query is needed for an empty changed-today group; unresolved
mappings remain explicit partial failures even if no fields can be queried.

Apply returned values to the existing TPSC objects, decoding rich text/enums
and clearing stale values to null only for successfully returned empty fields.
Missing/failed fields remain flagged, not fabricated. Preserve unrelated values,
array membership, order, nesting, request status, and historical activity.
For rich text, flatten confirmed Draft.js values by joining `blocks[].text`
with newlines; decode enums using resolved metadata. If an existing activity
array has no snapshot for that record's confirmed update date, prepend its own
corrected-state snapshot using the native update timestamp. Never borrow another
record's state or claim a generated snapshot is a separate Workfront event.
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
text. Either way, include a short **Workfront freshness** line with actual
requests/projects checked versus distinct valid IDs collected, records refreshed,
unresolved records, and missing-ID entries. Also report the number of actual
timestamp-query and field-refresh-query calls; zero refresh calls is valid when
no records changed today. Counts must come from this invocation's evidence, not
planned calls or TPSC timestamps. Keep net-new/renewal separate and avoid
duplicate project totals.

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
- `reference/same-day-refresh.md`: supporting shared refresh details; the inline
  timestamp-call and completion gates above must also be executed.
