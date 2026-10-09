# Mandatory per-ask same-day refresh

Use this procedure for summary and detail outputs before text, widgets, or
adapted files. Identical local copies keep all three read skills self-contained.
No private field map, tenant identifier, or production endpoint is included.

## Collect the returned records

- Summary: top-level projects and requests; inspect whether request GUIDs are
  named `tpscrequestid` in the advertised response.
- Request details: top-level projects and requests; request GUIDs are
  `tpsrequestid` in the documented detail response.
- Opportunity details: projects with their own nested requests; request GUIDs
  are `tpsrequestid`.

Use native project GUIDs (`tpsprojectid`) independently of requests. Collect
every returned record, deduplicate queries by GUID, and apply corrections to
every occurrence. Never discover additional records or substitute a name/DR
for a GUID. Programs are not refresh targets. Missing/ambiguous IDs are flagged,
not silently counted as an empty collection.

## Discover fields and check timestamps

Discover the authorized Workfront tools through the host's tool mechanism.
Initialize a new insights session with usage docs and entities; read filter
and date documentation before building queries. Read `reference/native-id-dictionary.md`;
the TPSC/native ID mapping is fixed, not a field-discovery task. Reuse known
connector ID paths (insights projects use `project.project_ID`). Resolve missing
native-ID connector syntax once per session/root, and resolve timestamp/custom
paths separately when absent. Do not guess issue/program paths or private mappings.
Report tool discovery, authorization, resolution, and query errors explicitly.

On **every new ask**, batch issue and project reads for native ID plus update
timestamp, mapping results by ID rather than result order. Exhaust pagination
according to connector limits. There is no one-hour or same-session record
cache. Prior metadata may be reused; previous-ask record values may not.

Use one timezone: the session's explicit timezone, otherwise UTC, interpreting
timestamp offsets before comparing calendar dates. Use Workfront's native
timestamp, never TPSC snapshot/history dates, to determine whether a record
was updated today.

Today's records require the fuller read below. Valid earlier timestamps leave
the entry as returned, but do not prove that older TPSC changes are synchronized.
Missing/malformed/future/unmatched timestamps remain unresolved with a warning.
Live results from this same invocation may satisfy corresponding reads.

## Refresh confirmed semantic mappings

Discover configured fields for the following meanings and confirm the mapping
from current metadata/tool documentation before overwriting a TPSC value:

| Root | Workfront meaning to discover | TPSC destination |
| --- | --- | --- |
| issue | Request management stage | `requeststage` |
| issue | Request management health | `requesthealth` |
| issue | Request blocker information | `blockerinfo` |
| issue | Request latest update/comment | `latestcomment` |
| project | Technical-case completion status | `techcasestatus` |
| project | Technical-risk mitigation comments | `techriskcomments` |

No static custom-field names or private ID mappings are assumed. A provider
narrative with a similar name is not proof of a matching refresh source.
If a mapping is ambiguous or cannot be confirmed, retain the source snapshot
value and report that field as unrefreshed. Do not repeatedly fetch TPSC as a
substitute for live Workfront.

Batch today's issue/project reads, including native IDs. Overwrite only the
confirmed fields on the existing objects, decoding enums/rich text through
metadata. Successfully returned empties clear stale values to null; failed or
absent fields do not. Preserve unrelated values, request status unless separately
confirmed, array membership/nesting, and existing activity history.

If an existing activity array lacks a snapshot for today's confirmed update,
a corrected-state snapshot may be prepended with the native update timestamp.
Do not rewrite historical entries or describe a generated snapshot as a
separate historical Workfront event.

## Gate the output

Each collected GUID must have a timestamp result or an explicit failure, and
each record changed today must have corrections or an explicit partial failure.
Pass corrected objects to text, widgets, and adapted files, never the original
stale snapshot. Include checked/refreshed counts and unresolved mappings/errors.
Keep usable TPSC data on failure, clearly labeled unrefreshed or partially
refreshed; put limitations in context data-quality flags as applicable.
Do not publish generated records, identities, links, or credentials here.
