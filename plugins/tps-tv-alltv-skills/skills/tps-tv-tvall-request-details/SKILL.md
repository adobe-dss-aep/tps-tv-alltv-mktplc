---
name: tps-tv-tvall-request-details
description: Gather structured Technical Validation context for an existing Workfront request, enriched by an authenticated tps-tv-alltv-assist connector. Use for a request URL, reference number, or account lookup resolving to a submitted request. Route pre-request opportunities and portfolio summaries to their dedicated skills.
metadata:
  version: "1.0.0"
  visibility: public
---

# Technical Validation Request Details

## Prerequisites and field discovery

Use only connected, authorized MCP tools. Do not call Workfront REST endpoints,
guess tenant IDs, fabricate record URLs, or invent data. If a connector is missing
or authorization fails, report that limitation before proceeding.

For a new Workfront session, read the connector's usage documentation with
`insights_read_docs("mcp-usage")` and list supported entities with
`insights_list_entities`. Discover fields with `insights_search_fields` and resolve
their relationship paths with `insights_get_field_paths`. Read the connector's
conditions, implicit-patterns, status, and date documentation before using the
corresponding filters. Resolve named accounts, users, and portfolio scope through
documented lookup tools. Never assume a custom field's ID or relationship path.
If resolution fails, report the unresolved field; do not substitute a guessed path.

## Workflow

1. Resolve the anchor request from a supplied URL, numeric reference, or scoped
   account/name lookup. Ask for clarification if several requests match. Fetch the
   issue and its parent opportunity project using resolved fields. An opportunity
   with no request belongs to `tps-tv-tvall-opp-details`.
2. Once verified `tpsaccountid`, `tpsprojectid`, and `tpsrequestid` values are known,
   call `tps_tv_read_tpsc_request_detail` before deep Workfront extraction. This is
   a data read, not a widget display or upload. If Workfront is unavailable, use
   verified IDs supplied by the user or existing authorized context; never
   manufacture missing IDs. Identify connector-only results as partial.
3. Gather authorized request and project data: objectives, use cases, scope,
   account firmographics, owners, dates, status, risks, and opportunity value.
   Discover configured custom fields at runtime. Keep net-new ARR, renewed ARR,
   and their grand total distinct; capture available per-solution values without
   assuming that missing amounts are zero.
4. Retain related records only when returned by the detail tool. Do not discover
   or fetch sibling opportunities independently. Attribute every captured field
   to its source, expose conflicts, and deduplicate narrative without discarding
   distinct facts.
5. Populate `reference/context-schema.json`. Preserve Workfront-sourced values
   and TPSC data separately rather than silently overwriting one with the other.
   Use null and a data-quality flag for unavailable fields. Do not store passwords,
   bearer tokens, or other credentials found in source text or links.
6. Check returned records for same-day Workfront changes using resolved update
   fields. Reuse already-refreshed records within the session. Refresh changed
   fields from Workfront, not by repeatedly calling a potentially cached TPSC
   read. Only update fields actually returned by the refresh; preserve unrelated
   history and values.
7. For widget output, call `tps_tv_read_tpsc_request_detail_widget` separately
   with the gathered data according to its advertised input schema. Skip this
   call for conversational output. Report unavailable presentation tools instead
   of claiming that a widget was displayed.
8. Write `context-<account-slug>.json` in the user's private working environment
   and summarize the account, request, opportunity, value, timeline, risks, and
   quality flags. Do not write generated customer context into this public repo.

If the user requests a pipeline overview instead of one anchored request, use
`tps-tv-tvall-my-opp-summary`. SharePoint attachments are a separate, explicit
write intent handled by `tps-tv-tvall-add-to-sharepoint`; never trigger them
automatically after a read.

## Output templates

- `reference/context-schema.json`: empty context shape, not a formal validator.
- `reference/tpsc-request-details-submission-schema.json`: a reduced submission
  shape with root-level IDs and a single account, project, and request.

Check the connected tools' current input schemas before sending a payload.
Do not send the whole working context to a tool that expects a reduced shape.
