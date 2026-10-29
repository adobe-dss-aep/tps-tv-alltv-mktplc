# Native identity dictionary

| TPSC field | Workfront identity | Provider ID |
| --- | --- | --- |
| `tpsrequestid` | `issue.id` | `meta.workfront_ids.request_id` |
| `tpscrequestid` (summary response alias) | `issue.id` | `meta.workfront_ids.request_id` |
| `tpsprojectid` | `project.id` | `meta.workfront_ids.project_id` |
| `tpsaccountid` | `program.id` | `meta.workfront_ids.program_id` |

These are the same native ID values, not custom-field values or lookup keys.
Do not search for a Workfront custom field named `tpsprojectid`, `tpsrequestid`,
or `tpsaccountid`. Do not re-resolve a supplied native ID by account name, DR,
CRM ID, or reference number. Keep the exact returned value; never fabricate IDs.
An ID still requires authorized live reads; knowing its mapping is not freshness.
Programs identify accounts but are not project/issue freshness targets.

## Connector paths versus identities

`project.project_ID` is the confirmed insights connector field ID for native
`project.id`. Use it directly with that connector's advertised filter/selection
schema; do not rediscover it on every ask. Exact field IDs are case-sensitive.
No exact issue/program connector field IDs are established by this dictionary.
Use already documented or successfully resolved native-ID paths; if absent,
resolve only the connector syntax for the known `issue.id`/`program.id`, once
per session/root. Do not guess those paths from the project naming pattern.
Resolve native timestamp and custom refresh paths separately when needed.
Reuse successful metadata, not old record values. If a known path is rejected,
report the error, resolve the replacement once, and retry using current metadata.

For insights result cells such as `{"value": "<native ID>"}`, read the `value`
member before matching by GUID. Map by ID, not row order; preserve field values,
decode rich text separately, and never substitute a project name's URL for an ID.
Keep identical copies in the provider and two Workfront-reading detail adapters.
