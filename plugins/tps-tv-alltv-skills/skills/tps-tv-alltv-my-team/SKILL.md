---
name: tps-tv-alltv-my-team
description: Show the signed-in user's My Team (tps-tv-myteam) interactive widget through tps_tv_read_direct_reports. Use for "show my team", "my direct reports", or an explicit My Team widget request. This tool fetches and renders the team widget itself; do not gather opportunity summaries or Workfront context. A person's pipeline belongs to tps-tv-tvall-my-opp-summary.
metadata:
  version: "1.0.0"
  visibility: public
---

# My Team

## Purpose and scope

Display the `tps-tv-myteam` widget for the signed-in user through the authorized
`tps-tv-alltv-assist` connector. `tps-tv-myteam` is the widget's name, not a
separate MCP tool. The interactive `tps_tv_read_direct_reports` tool fetches
the data and renders the widget in one call.

This is a standalone team readout. It does not require the CXL context provider,
perform Workfront freshness checks, or build a team pipeline. Installation
does not grant access; the connector must enforce authorization.

## Workflow

1. For a My Team/direct-reports request, discover/load
   `tps_tv_read_direct_reports` through the host's tool-discovery mechanism.
   Inspect its current advertised schema and use the exact advertised name,
   including its server namespace when present. Initially hidden tools are
   not proof that the connector is unavailable.
2. Use the signed-in user's default identity. Omit `displayName` and `email`;
   these are testing-only identity overrides, not skill display-name settings.
   Do not infer a manager from conversation history or ask for identity fields.
   If the user requests another manager's team, explain that this skill only
   opens the signed-in user's team; do not silently substitute that team or
   attempt an identity override.
3. Call once per new ask with an empty argument object `{}` when the advertised
   schema permits it. If the schema no longer permits the signed-in-user
   invocation, report the incompatibility rather than guessing arguments.
   Do not reuse an earlier roster as a fresh result.
4. Let the tool's interactive response be the answer. Do not call a separate
   widget, dump raw JSON, or fabricate a team table. Keep any accompanying text
   to a short pointer and actual limitations. Report discovery, authorization,
   tool, or rendering errors explicitly; never claim the widget was shown after
   a failure. A data-only result is a presentation limitation, not a successful
   widget display. Treat an empty team as confirmed only when the tool returns it.

Do not call `tps_tv_read_tpsc_user_summary` for each team member, enumerate
opportunities, invoke `get-tps-central-context`, or run the summary refresh phase.
A subsequent person's pipeline request goes to `tps-tv-tvall-my-opp-summary`
with the user's supplied target, not an inferred member.

This dedicated widget request does not ask about widgets versus text and does
not overwrite `presentationPreference.useWidget`. Preserve any existing
summary/request/opportunity readout preference on follow-ups.
