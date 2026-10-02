# tps-tv-alltv-mktplc

A public Claude marketplace containing the `tps-tv-alltv-skills` plugin for
Technical Validation workflows. This repository remains a **marketplace**; its
plugin lives under `plugins/tps-tv-alltv-skills/`.

## Skills

- `tps-tv-tvall-request-details`: gather context for an existing validation request.
- `tps-tv-tvall-opp-details`: gather context for an opportunity before a request exists.
- `tps-tv-tvall-my-opp-summary`: summarize the current user's or a named user's pipeline.
- `tps-tv-tvall-add-to-sharepoint`: attach an asset only when explicitly requested.

## Installation and prerequisites

In a Claude environment that supports GitHub marketplaces, add
`adobe-dss-aep/tps-tv-alltv-mktplc` as the marketplace source and install
`tps-tv-alltv-skills`. Follow the installation flow provided by that environment.

Configure the Adobe Workfront MCP and an authenticated `tps-tv-alltv-assist`
connector separately through your client's connector settings. Obtain the approved
server URL and access requirements from your administrator. This public repository
does not bundle an MCP endpoint, token, client secret, or tenant configuration.
Installing the plugin does not grant access to Workfront, SharePoint, or other
connected systems. The servers must enforce authorization independently.

The assistant must discover entity fields and relationship paths through the
connected Workfront toolset rather than using tenant-specific identifiers. Missing
connectors, inaccessible records, and unresolved fields must be reported explicitly.

## Public distribution scope

This is a new, public-safe distribution with fresh Git history. It contains
generalized skill instructions and empty context/submission templates, not
customer-derived examples, populated context files, private field dictionaries,
tenant-specific IDs, or the original repository history.

Version `1.0.0` deliberately differs from the internal distribution: no bundled
production connector and no private reference mappings. Full operation requires
connector setup, runtime field discovery, and potentially tenant-specific
configuration supplied privately by an administrator. Live tool execution is not
validated by this repository's structural checks.

The JSON files called `*-schema.json` are empty output-shape templates, not formal
JSON Schema validators. Fill them only with authorized data gathered at runtime.
Never commit generated customer context, user identities, credentials, or uploads
to this public repository.

## Maintenance

1. Add or update skills under `plugins/tps-tv-alltv-skills/skills/`.
2. Keep each skill's frontmatter name consistent with its directory.
3. Keep the two submission-template copies synchronized.
4. Bump the plugin version for changes; use a major version for behavior changes.
5. Review every file for public-release suitability before publishing.
6. Submit changes through a pull request.
