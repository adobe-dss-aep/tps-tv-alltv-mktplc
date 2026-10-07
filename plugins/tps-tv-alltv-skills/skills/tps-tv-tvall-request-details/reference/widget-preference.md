# Shared TV/AllTV widget preference

Read this before routing and again before presenting a summary, request detail,
or opportunity detail. Identical local copies keep all three skills self-contained.
This preference controls presentation only, never whether freshness checks run.

## Logical conversation state

Maintain the conversation setting `presentationPreference` with a boolean
`useWidget` and `source` (`explicit`, `inferred`, or `default`). This is logical
conversation/handoff state, not a claim that the host provides a persistent
settings API. Recover it from the user's latest choice and prior handoffs when
necessary; do not invent a storage tool or require a settings-file write.

Resolve in this order:

1. The current user's explicit choice/change.
2. The most recent explicit choice earlier in this same conversation, including
   the answer to summary onboarding.
3. The previously resolved conversation/handoff setting, unless contradicted
   by a newer user choice.
4. Prior widget interaction, only if no resolved choice exists.
5. A default of false, only if no choice/state/interaction exists and summary
   onboarding below does not apply.

Both `useWidget: true` and `useWidget: false` are resolved choices. Never treat
false as missing, re-default true to false on a follow-up, or infer text preference
from a tool's lack of a widget. A missing boolean in a tool response/provider file
does not erase the conversation setting. "Show that request", "more detail", or
switching skills is not a change of preference. Explicit choices beat inference.

## One-time summary onboarding

If My Opportunity Summary opens the TV/AllTV conversation block and there is
no resolved preference or prior summary/detail presentation in this conversation,
briefly explain and ask **once before fetching data**:

"I can show your pipeline in interactive widgets or as conversational text.
Which would you prefer?"

Use the host's question/choice interface when available, with "Interactive
widgets" and "Conversational text". Wait for the answer and record an explicit
boolean, true or false respectively. Retain the original pipeline target and
resume that ask; the answer selects presentation, not a new person/deal lookup.
If the original ask already explicitly requests widgets/text, record it and
skip onboarding. Do not ask again on follow-ups or adapter handoffs. If the user
declines to choose but asks to proceed, set false with source default and continue.

## Handoffs and output gates

Pass `presentationPreference` alongside the anchor/provider result on logical
skill handoffs: summary to either detail skill, and either detail skill to the
other. Recheck the latest conversation choice when returning from the context
provider, rather than resetting to a skill-local default.

Do not send this object as an extra MCP tool argument or an unsupported provider
parameter. Provider `presentation: return_to_caller` suppresses its own summary;
it does **not** mean `useWidget: false` for the adapter.

Before text/widget output, recover and verify the resolved boolean:
- True: invoke the appropriate advertised widget tool with freshness-corrected
  data. Keep accompanying text to a pointer, freshness counts, and warnings.
- False: present the corrected result conversationally, with no readout widget.
- A missing/failed widget tool: explicitly report the limitation; a text fallback
  is allowed only as a labeled fallback, without silently changing the preference.

Detail adapters store the resolved object in their adapted file under
`presentationPreference`, not in the provider source or widget `data` payload.
Upload widgets are an independent required action interface; opening an upload
does not opt the user into readout widgets or change this setting.
