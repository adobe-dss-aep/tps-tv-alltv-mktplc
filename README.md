# tps-tv-alltv-mktplc

A public Claude marketplace containing `tps-tv-alltv-skills` and
`cxl-workbench-alltv` for Technical Validation workflows. Both plugins live
under `plugins/`; this repository remains a **marketplace**.

## Skills

- `get-tps-central-context` (CXL plugin): gather the main Workfront context once
  and validate its schema 2.1 provider contract.
- `tps-tv-tvall-request-details`: adapt provider context for an existing request,
  enriching it with TPSC history and SharePoint metadata.
- `tps-tv-tvall-opp-details`: adapt provider context for a pre-request opportunity.
- `tps-tv-tvall-my-opp-summary`: summarize the current user's or a named user's pipeline.
- `tps-tv-alltv-my-team`: open the signed-in user's `tps-tv-myteam` interactive widget through `tps_tv_read_direct_reports`, without gathering team pipelines or Workfront context.
- `tps-tv-tvall-add-to-sharepoint`: attach an asset only when explicitly requested.

## Installation and prerequisites

In a Claude environment that supports GitHub marketplaces, add
`adobe-dss-aep/tps-tv-alltv-mktplc` as the marketplace source and install
**both** `tps-tv-alltv-skills` **3.0.0** and `cxl-workbench-alltv` **1.2.2**
for full-context workflows. Follow the installation flow provided by that
environment. The provider is a skill-level dependency, not an automatically
installed package.

Configure the Adobe Workfront MCP and an authenticated `tps-tv-alltv-assist`
connector separately through your client's connector settings. Obtain the approved
server URL and access requirements from your administrator. This public repository
does not bundle an MCP endpoint, token, client secret, or tenant configuration.
Installing the plugin does not grant access to Workfront, SharePoint, or other
connected systems. The servers must enforce authorization independently.

The assistant must discover entity fields and relationship paths through the
connected Workfront toolset rather than using tenant-specific identifiers. Missing
connectors, inaccessible records, and unresolved fields must be reported explicitly.

## Shared provider and freshness

My Team is a standalone roster widget and needs only the authorized TPSC
connector, not the CXL provider or Workfront. It uses the signed-in identity
without testing overrides and preserves the saved widget/text preference for
other readouts. Its skill identifier is `tps-tv-alltv-my-team`; its readable
heading is **My Team**. There is no standard separate skill display-name field.

The detail skills invoke the installed `get-tps-central-context` skill with
`context_scope: anchor_only` and `presentation: return_to_caller`. The provider
owns anchor resolution, deep fields, people enrichment, provenance, conflicts,
and validation. The adapters shape that result into their existing request/
opportunity contracts, separately adding TPSC-native data and presentation.
They do not restore a duplicate deep gather if the provider is missing.

Request details retains seven runtime references; opportunity details retains
six. These cover the native-ID dictionary, provider invocation/mapping, the adapter output template,
same-day refresh, widget preference, and (request only) the upload submission
shape. The templates remain complete for output compatibility, but their common
fields are copied from the provider, not independently gathered. Deep-field
discovery belongs to the provider; no legacy gathering maps, dictionaries, or
populated examples are packaged in the detail skills.

The [native-ID dictionary](plugins/cxl-workbench-alltv/skills/get-tps-central-context/reference/native-id-dictionary.md)
is identical in the provider and both Workfront-reading detail skills:
`tpsrequestid` (summary alias `tpscrequestid`) equals `issue.id`,
`tpsprojectid` equals `project.id`, and `tpsaccountid` equals `program.id`.
These are native values, not custom-field lookups. The confirmed insights
project path is `project.project_ID`; other native-ID connector syntax is
resolved only when absent and reused in-session. Native live timestamp checks
remain mandatory. No customer record, custom-field ID, or tenant URL from a
trace is needed to encode these identity relationships.

### Reduced reads and deterministic enrichment

Full-context/artifact asks retain `context_profile: full`. Known-ID status
asks still bypass the provider. Widget/status asks that need anchor resolution,
and explicitly requested widget enrichment, use `context_profile:
widget_enrichment` with `anchor_only`. The selected profile depends on content,
not on the widget/text boolean. Reduced context cannot ground a full artifact.

Tune selected Workfront meanings in the provider's
[query profile](plugins/cxl-workbench-alltv/skills/get-tps-central-context/reference/query-profiles.md).
It requires documented field projection instead of broad summaries, excludes
unneeded deep layers, and reports an explicit limitation when projection is not
supported. Profile/read-evidence metadata extends schema 2.1 compatibly; old
full results remain accepted. No measured response-size savings are claimed
without a live connector trace.

Tune exact provider-to-native destinations in
[widget mapping](plugins/tps-tv-alltv-skills/skills/tps-tv-tvall-request-details/reference/widget-mapping.md)
and the shared
[mapping helper](plugins/tps-tv-alltv-skills/scripts/map_widget_enrichment.py).
Both adapters execute the mapping after selection and freshness. The helper
matches native GUIDs, preserves unrelated records/history/SharePoint, copies
only confirmed reduced-profile enrichment, and reports incompatible inputs.
It writes only the native widget envelope, not preference/provider metadata.
Python/file execution is optional for the mapper: unsupported hosts explicitly
report manual mapping and follow the same guarded table. Full provider
validation still requires Python as before.

The helper measures mapping milliseconds, provider file bytes, and serialized
widget-data bytes separately. Workfront response bytes and call counts must be
measured at the actual tool boundary when observable; a trimmed provider file
is not evidence of raw response-size reduction. TPSC history is not truncated.

The provider defaults to `family` scope for standalone use, using only
documented authorized relationships. It accepts typed native IDs without
constructing Workfront URLs. No private maps or dictionaries are bundled.

Every new detail status/context ask checks native Workfront update timestamps in
batches, with no one-hour or same-session record skip. Records updated today
are corrected through confirmed runtime semantic mappings before text, widget,
or adapted-file output. Missing mappings/errors remain explicit partial-refresh
limitations; repeated TPSC fetches are not a freshness substitute.

Portfolio summaries stay lightweight and invoke the provider only for a
full-context follow-up through a detail adapter. Uploads use a complete supplied
payload directly, or get the request adapter's enriched output. A raw provider
file is not a widget or upload payload.

Opportunity summaries use only `tps_tv_read_tpsc_user_summary`. They never
discover or call Workfront, refresh timestamps, gather context, or enrich results
through another tool, even on failure or an explicit freshness request.
The model writes a conversational answer grounded in the returned data by
default, without a blocking presentation question. The summary widget is
explicit opt-in only: a current request or prior explicit readout choice in
the conversation, not inferred interaction or an inherited default true.
Widget data is the summary tool's returned arrays, without external enrichment.

Separate user-requested detail follow-ups retain their existing Workfront
freshness policies and receive the resolved presentation preference. A summary
never dispatches detail reads to supplement its own answer. Summary-only
operation requires neither Workfront nor the CXL provider. Structural tests
guard this boundary; live execution still needs verification in the client.

## Public distribution scope

This is a new, public-safe distribution with fresh Git history. It contains
generalized skill instructions and empty context/submission templates, not
customer-derived examples, populated context files, private field dictionaries,
tenant-specific IDs, or the original repository history.

This distribution deliberately differs from the internal distribution: no bundled
production connector and no private reference mappings. Full operation requires
connector setup, runtime field discovery, and potentially tenant-specific
configuration supplied privately by an administrator. Live tool execution is not
validated by this repository's structural checks.

Skill-local `context-schema.json` and submission references are empty output
shapes. The CXL plugin's `schemas/context.schema.json` is a formal JSON Schema
contract checked by its standard-library Python validator. Fill context shapes
only with authorized data gathered at runtime.
Never commit generated customer context, user identities, credentials, or uploads
to this public repository. Root-level generated context files are ignored as a
convenience; keep runtime outputs in a separate private working directory.

## Maintenance

1. Add or update skills under `plugins/tps-tv-alltv-skills/skills/`.
2. Keep each skill's frontmatter name consistent with its directory.
3. Keep the two submission-template copies synchronized.
4. Bump the plugin version for changes; use a major version for behavior changes.
5. Review every file for public-release suitability before publishing.
6. Submit changes through a pull request.

## Validation

With Python 3, run the synthetic provider/adapter contract tests from the
marketplace checkout:

```text
python -m unittest discover -s plugins/cxl-workbench-alltv/tests -p "test_*.py"
python -m unittest discover -s plugins/tps-tv-alltv-skills/tests -p "test_*.py"
```

Structural tests do not validate live connector execution. After updating
Claude Desktop, test an authorized record updated today and repeat after
another change within an hour. Verify corrected values in text and widgets,
and explicitly reported limitations when a field cannot be resolved.
