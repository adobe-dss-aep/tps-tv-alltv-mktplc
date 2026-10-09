# Provider enrichment to TPSC mapping

Run after sibling eligibility, request selection, and same-day refresh.
The input is the corrected native widget envelope, not raw provider context.
Match by verified GUIDs, never array order. The mapping helper does not fetch,
filter, refresh, mark primary requests, lift SharePoint, or shape upload data.
Those operations remain the adapter's existing steps.

| Provider source | Matching destination |
| --- | --- |
| `account_firmographics.sub_name` | Primary `accounts[].sub_name` |
| `objectives` | Primary `projects[].objectives` |
| `use_cases` | Primary `projects[].use_cases` |
| `influenced_pipeline_usd` | Primary `projects[].influenced_pipeline_usd` |
| `record_links.primary_opportunity_project` | Request adapter primary `projects[].primary_opportunity_link` |
| `record_links.tv_request_issue` | Request adapter primary `requests[].tv_request_link` |
| `products_in_scope` | Request adapter primary `requests[].products_in_scope` |
| `timeline` | Request adapter primary `requests[].timeline` |

Provider `meta.workfront_ids` identifies the primary account/project/request;
it does not replace native widget ID fields. A missing/mismatched ID blocks
mapping and must be reported. Do not fabricate IDs or accounts.

For reduced results, copy only paths listed in `meta.enrichment_fields`.
Confirmed empties may clear the mapped enrichment value. Unselected, failed,
or excluded paths leave TPSC values intact. For legacy full results without
read evidence, copy nonempty enrichment only; do not clear native values from
unknown template placeholders. Never copy provider `engagement.latest_update`
over native `latestcomment`; freshness uses its separately confirmed sources.
Request fields are never copied into secondary requests or nested opportunity
requests. Preserve all unrelated fields, activity, SharePoint, arrays, and order.
The same-invocation corrections win over old snapshots.

## Execute the helper

When Python/file execution is available, use the installed TPS plugin's reachable
`${CLAUDE_PLUGIN_ROOT}/scripts/map_widget_enrichment.py`:

```text
python <resolved-script-path> request <provider-file> <corrected-widget-data-file> <output-file>
python <resolved-script-path> opportunity <provider-file> <corrected-widget-data-file> <output-file>
```

Use only the matching adapter kind, in the user's private working directory,
not in the plugin checkout. Pass the already filtered/corrected envelope.
Use the output as widget `data`; copy its primary records into the adapted
file while retaining the existing lifted SharePoint and array-nesting rules.
Full-context output retains all provider common layers separately.
Do not put the printed mapping report, provider metadata, or preference inside
widget `data`. The report measures mapping time, provider file bytes, and widget
data bytes; it does not measure raw Workfront response bytes.

If script execution is unavailable, report that limitation and apply this exact
table manually with the same guards. If execution fails, report its FAIL error
and do not claim successful mapping or silently render unprocessed data.

Keep this local contract identical in both adapters; the helper's `MAPPINGS`
is the executable mapping. Changes must update the table and mapping tests.
