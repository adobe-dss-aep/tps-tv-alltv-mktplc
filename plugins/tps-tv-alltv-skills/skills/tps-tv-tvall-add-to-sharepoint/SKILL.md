---
name: tps-tv-tvall-add-to-sharepoint
description: Attach a file or link to SharePoint for a specific Technical Validation request through an authorized tps-tv-alltv-assist connector. Run only for an explicit attachment request, using supplied or previously gathered context and the connector's upload widget.
metadata:
  version: "1.0.0"
  visibility: public
---

# Attach an Asset to SharePoint

This is an explicit write action, never an automatic follow-up to a context read.
The connector must enforce authorization independently of plugin installation.

## Workflow

1. Check whether the invocation already contains a populated authorized account,
   project, request, and SharePoint payload, for example from a detail widget.
   If supplied, use that payload without another Workfront or TPSC read.
2. Otherwise use the unambiguous request already gathered in this session. If
   several requests could match, ask which one. If the target context is missing,
   invoke `tps-tv-tvall-request-details` and return here. Never infer the target
   from a filename or guess an account/project/request ID.
3. Use `reference/tpsc-request-details-submission-schema.json` as the reduced
   account/project/request shape. Reduce any request array to the target entry
   and exclude `is_primary` and generated activity history from that reduced
   submission. SharePoint metadata is a separate input, not a field in this
   template.
4. Inspect `tps_tv_add_to_sharepoint`'s advertised input schema and call it using
   the supplied account, project, request, and SharePoint data. The upload widget
   is the required interface for file/link selection; do not request uploads or
   credentials in chat. Only omit fields or use empty pre-upload values if the
   tool's schema and documented widget flow explicitly permit them. If an input
   is required but unavailable, report the blocking requirement rather than
   guessing a value or sending an invalid payload.
5. Let the user complete selection and submission through the widget. A rendered
   widget alone is not evidence that an upload succeeded. Report completion only
   after the connector confirms it; surface tool failures explicitly.

## Data handling

Do not publish payloads, uploads, SharePoint links, credentials, or generated
request context to this public repository.

The submission reference is an empty shape template, not a formal JSON Schema.
Keep it synchronized with the copy in `tps-tv-tvall-request-details/reference/`.
