#!/usr/bin/env python3
"""Validate a TPS Central context against its JSON Schema. Standard library only.

Usage:
  python3 scripts/validate.py path/to/doc.json [schema]

`schema` may be a path to a .json schema, or the shorthand `context`.
When omitted the schema defaults to `context`. Schemas
resolve under <plugin root>/schemas/, honoring CLAUDE_PLUGIN_ROOT.

Prints one FAIL line per violation (with the JSON path to the offending value)
and exits 1; prints PASS and exits 0 when the document conforms.

Supports the draft-07 subset these contracts use: type (including a list of
types), required, properties, additionalProperties, enum, items, minItems,
maxItems, pattern, and allOf. Extend `_validate` if the contracts grow beyond
this set.
"""
import json
import os
import pathlib
import re
import sys

_ROOT = pathlib.Path(os.environ.get(
    "CLAUDE_PLUGIN_ROOT", pathlib.Path(__file__).resolve().parent.parent))
SCHEMA_DIR = _ROOT / "schemas"
SHORTHANDS = {
    "context": "context.schema.json",
}

_TYPES = {
    "object": dict, "array": list, "string": str, "integer": int,
    "number": (int, float), "boolean": bool, "null": type(None),
}


def _type_ok(value, t):
    py = _TYPES.get(t)
    if py is None:
        return True
    if t == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if t == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if t == "boolean":
        return isinstance(value, bool)
    return isinstance(value, py)


def _validate(value, schema, path, errs):
    for sub in schema.get("allOf", []):
        _validate(value, sub, path, errs)

    if "enum" in schema and value not in schema["enum"]:
        errs.append(f"{path or '(root)'}: {value!r} is not one of {schema['enum']}")

    t = schema.get("type")
    if t is not None:
        types = t if isinstance(t, list) else [t]
        if not any(_type_ok(value, tt) for tt in types):
            errs.append(f"{path or '(root)'}: expected type {t}, got {type(value).__name__}")
            return

    if isinstance(value, dict):
        _validate_object(value, schema, path, errs)
    elif isinstance(value, list):
        _validate_array(value, schema, path, errs)
    elif isinstance(value, str):
        pat = schema.get("pattern")
        if pat is not None and re.search(pat, value) is None:
            errs.append(f"{path or '(root)'}: {value!r} does not match pattern /{pat}/")


def _validate_object(value, schema, path, errs):
    for req in schema.get("required", []):
        if req not in value:
            errs.append(f"{path}.{req}".lstrip(".") + ": required property is missing")
    props = schema.get("properties", {})
    addl = schema.get("additionalProperties", True)
    for k, v in value.items():
        child = f"{path}.{k}".lstrip(".")
        if k in props:
            _validate(v, props[k], child, errs)
        elif addl is False:
            errs.append(f"{child}: property is not allowed (additionalProperties is false)")
        elif isinstance(addl, dict):
            _validate(v, addl, child, errs)


def _validate_array(value, schema, path, errs):
    if "minItems" in schema and len(value) < schema["minItems"]:
        errs.append(f"{path or '(root)'}: has {len(value)} items, minimum is {schema['minItems']}")
    if "maxItems" in schema and len(value) > schema["maxItems"]:
        errs.append(f"{path or '(root)'}: has {len(value)} items, maximum is {schema['maxItems']}")
    items = schema.get("items")
    if isinstance(items, dict):
        for i, item in enumerate(value):
            _validate(item, items, f"{path}[{i}]", errs)


def resolve_schema(arg, doc_path):
    if arg is not None:
        return SCHEMA_DIR / SHORTHANDS[arg] if arg in SHORTHANDS else pathlib.Path(arg)
    return SCHEMA_DIR / SHORTHANDS["context"]


def validate_context_profile(doc, errs):
    meta = doc.get("meta") if isinstance(doc, dict) else None
    if not isinstance(meta, dict) or meta.get("context_profile", "full") != "widget_enrichment":
        return
    if meta.get("context_scope") != "anchor_only":
        errs.append("meta.context_scope: widget_enrichment requires anchor_only")
    if "enrichment_fields" not in meta:
        errs.append("meta.enrichment_fields: widget_enrichment requires explicit read evidence")
    if not doc.get("data_quality_flags"):
        errs.append("data_quality_flags: reduced context must declare its limitations")


def main(doc_path, schema_arg=None):
    doc_p = pathlib.Path(doc_path)
    schema_p = resolve_schema(schema_arg, doc_path)
    if not doc_p.exists():
        print(f"FAIL cannot read document: {doc_p}")
        return 1
    if not schema_p.exists():
        print(f"FAIL cannot read schema: {schema_p}")
        return 1
    try:
        doc = json.loads(doc_p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"FAIL {doc_p.name} is not valid JSON: {e}")
        return 1
    schema = json.loads(schema_p.read_text(encoding="utf-8"))

    errs = []
    _validate(doc, schema, "", errs)
    if schema_p.resolve() == (SCHEMA_DIR / SHORTHANDS["context"]).resolve():
        validate_context_profile(doc, errs)
    if errs:
        seen = set()
        for e in errs:
            if e not in seen:
                seen.add(e)
                print("FAIL " + e)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
