---
name: tps-tv-tvall-my-opp-summary
description: Summarize the signed-in user's or a named colleague's TV/AllTV opportunities and requests using only tps_tv_read_tpsc_user_summary. Never use the Workfront connector or a context provider for summaries. Default to a model-written conversational answer grounded in the returned data; display the summary widget only on explicit user opt-in. Use for my opportunities, my pipeline, open requests, or a colleague's opportunity summary.
metadata:
  version: "2.0.0"
  visibility: public
---

# Technical Validation Pipeline Summary

## Strict data boundary

The only data source is `tps_tv_read_tpsc_user_summary` on the authorized TPSC
connector. In no circumstances use the Workfront connector for a summary:
no tool discovery, timestamp checks, same-day refresh, field mapping, enrichment,
or fallback. Do not invoke a context provider or detail skill to assemble,
validate, repair, or supplement a summary. This applies to every portfolio
size, both presentation styles, and follow-up summary asks.

The only additional permitted tool is `tps_tv_read_tpsc_user_summary_widget`,
and only for explicitly opted-in display of the returned summary data. It does
not fetch or refresh anything. Do not use team, detail, or upload tools here.

## Step 0: Resolve presentation without blocking

Read `reference/widget-preference.md`. Conversational text is the default.
Do not ask a widget-versus-text onboarding question before fetching data.
Only a current explicit widget request or an earlier explicit readout opt-in
in this conversation enables the widget. Interaction with a widget, inferred
preference, a tool recommendation, or a default boolean is not explicit opt-in.
Honor a newer explicit request for text. Preserve the resolved
`presentationPreference` on later user-requested detail handoffs.

## Step 1: Fetch the authorized summary

Discover/load only the TPSC summary tool and inspect its advertised schema.
For "my" summary, use its documented signed-in-user default without guessing
identity fields. For a named colleague, pass only the user-supplied target
using supported arguments and authorization. Report ambiguous targets,
authorization failures, unavailable tools, and malformed responses explicitly.
Never look up a person or missing record through another connector.

Call `tps_tv_read_tpsc_user_summary` for each new summary data request. Follow
its documented pagination if applicable; do not silently truncate the roster.
Preserve the returned `projects` and `requests` arrays and native fields.
Missing fields are unknown, not a reason to enrich. A failed read is not an
empty portfolio. A confirmed empty roster may be reported as such.

## Step 2: Answer from the returned data

By default, write a conversational summary using model judgment to choose
useful structure, emphasis, and detail for the user's question. Ground every
fact in the tool result; distinguish project/request counts, avoid duplicate
project totals, and keep net-new and renewal separate when actually available.
Do not invent monetary splits, risks, status, missing values, or records.
Do not dump raw JSON or require a fixed prose template.

If explicitly opted in, call `tps_tv_read_tpsc_user_summary_widget` with
`data: { projects, requests }` from the summary result, unmodified by external
data. Do not add preference metadata as tool arguments or fields in `data`.
If the widget is unavailable or fails, report the limitation and provide a
clearly labeled conversational fallback without erasing the explicit preference.

Do not claim live Workfront verification or report Workfront freshness counts.
If source timestamps/limitations are relevant, describe only what the summary
tool actually returned. When freshness is questioned, explain this data boundary;
never perform a Workfront check, even on an explicit refresh request.

## Follow-up handoff

Only a separate user request for a specific request/opportunity's details may
hand off to `tps-tv-tvall-request-details` or `tps-tv-tvall-opp-details`.
Pass the user's supplied anchor or confirmed returned IDs and
`presentationPreference`. Do not automatically gather details while answering
the summary. Detail skills retain their own independent data/freshness policies.
