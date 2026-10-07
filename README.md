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
- `tps-tv-tvall-add-to-sharepoint`: attach an asset only when explicitly requested.

## Installation and prerequisites

In a Claude environment that supports GitHub marketplaces, add
`adobe-dss-aep/tps-tv-alltv-mktplc` as the marketplace source and install
**both** `tps-tv-alltv-skills` **2.0.0** and `cxl-workbench-alltv` **1.1.0**
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

The detail skills invoke the installed `get-tps-central-context` skill with
`context_scope: anchor_only` and `presentation: return_to_caller`. The provider
owns anchor resolution, deep fields, people enrichment, provenance, conflicts,
and validation. The adapters shape that result into their existing request/
opportunity contracts, separately adding TPSC-native data and presentation.
They do not restore a duplicate deep gather if the provider is missing.

The provider defaults to `family` scope for standalone use, using only
documented authorized relationships. It accepts typed native IDs without
constructing Workfront URLs. No private maps or dictionaries are bundled.

Every new status/context ask checks native Workfront update timestamps in
batches, with no one-hour or same-session record skip. Records updated today
are corrected through confirmed runtime semantic mappings before text, widget,
or adapted-file output. Missing mappings/errors remain explicit partial-refresh
limitations; repeated TPSC fetches are not a freshness substitute.

Portfolio summaries stay lightweight and invoke the provider only for a
full-context follow-up through a detail adapter. Uploads use a complete supplied
payload directly, or get the request adapter's enriched output. A raw provider
file is not a widget or upload payload.

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
```

Structural tests do not validate live connector execution. After updating
Claude Desktop, test an authorized record updated today and repeat after
another change within an hour. Verify corrected values in text and widgets,
and explicitly reported limitations when a field cannot be resolved.
