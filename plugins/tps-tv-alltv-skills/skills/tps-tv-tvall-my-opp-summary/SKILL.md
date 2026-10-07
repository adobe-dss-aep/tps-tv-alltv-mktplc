---
name: tps-tv-tvall-my-opp-summary
description: Summarize the signed-in user's or a named colleague's Technical Validation requests and opportunity pipeline through an authorized tps-tv-alltv-assist connector. Use for portfolio-level asks rather than full context for a single anchored request.
metadata:
  version: "1.1.0"
  visibility: public
---

# Technical Validation Pipeline Summary

## Workflow

1. Identify whether the ask concerns the current user or a named colleague.
   Resolve identity only with the connector's documented authenticated-user or
   named-user lookup mechanisms. If a name is ambiguous, ask for clarification.
   Never guess an email address, user ID, or tenant identifier.
2. Call `tps_tv_read_tpsc_user_summary` according to its advertised input schema.
   Report authorization failures or missing connectors explicitly. This skill
   does not independently enumerate every opportunity or run a full detail
   gather for each result.
3. Inspect the returned shape before reading IDs. The user-summary tool may use
   `tpscrequestid` where detail tools use `tpsrequestid`; do not silently read an
   absent field or join records by an assumed name.
4. Read and execute `reference/same-day-refresh.md` on every new ask. Discover
   and resolve native timestamp fields and confirmed semantic mappings, batch
   checks by returned GUID, and refresh today's records directly from Workfront.
   Do not reuse previous-ask record snapshots, even within an hour. Preserve
   unrelated values/history and report partial/unavailable refreshes explicitly.
5. Summarize the returned pipeline: scope, opportunities, requests, stages,
   relevant dates, risks, and values that the source actually supplies. Keep
   net-new and renewal amounts distinct. Do not manufacture totals or double
   count a project because it has several requests.
6. Respect conversational versus widget preference. Use a dedicated presentation
   tool only if the connector advertises one and the user prefers it; do not
   invent a tool name or claim a widget rendered without a successful call.
7. A follow-up asking for one item's full context is an anchored detail intent.
   Hand off to `tps-tv-tvall-request-details` for an existing request or
   `tps-tv-tvall-opp-details` for a pre-request opportunity.
   Those adapters invoke `get-tps-central-context` from required
   `cxl-workbench-alltv` 1.1.0 or later. Pass confirmed native IDs or original
   URLs/references; never run a full provider gather for every portfolio row.

## Data handling

Use only authorized records. Clearly label missing, partial, or stale results.
Never commit pipeline responses, customer details, user identities, credentials,
or generated reports to this public repository.
