# Summary presentation: conversational default, explicit widget opt-in

Resolve `presentationPreference` from the most recent explicit choice in this
conversation, current ask first. An explicit widget choice is
`{"useWidget": true, "source": "explicit"}`; an explicit text choice is
`{"useWidget": false, "source": "explicit"}`.

With no explicit choice, use `{"useWidget": false, "source": "default"}` and
answer conversationally immediately. No onboarding question or wait is needed.
Never infer widget opt-in from interactions, tool descriptions, an upload or
My Team widget, or a true boolean with inferred/default/unknown provenance.
An earlier explicit readout choice remains valid until the user changes it.

Pass the resolved choice on separate user-requested detail handoffs. Missing
preference fields in tool data do not erase an explicit choice. Preference is
logical conversation state, not a new storage API or MCP parameter. Keep it
outside widget `data` and provider inputs.

For true with explicit source, display only the summary tool's returned arrays
through its widget tool. Otherwise provide a model-written conversational answer.
On widget failure, report it and label any conversational fallback without
silently changing the preference. No presentation choice permits Workfront
access, enrichment, or freshness checks in this skill.
