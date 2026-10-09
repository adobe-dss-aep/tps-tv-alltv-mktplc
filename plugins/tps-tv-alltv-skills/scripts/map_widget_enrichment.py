"""Map provider enrichment onto already filtered, freshness-corrected TPSC data.

Usage: python map_widget_enrichment.py request|opportunity provider.json data.json output.json
No network calls, filtering, refresh, or upload shaping. Standard library only.
"""

import copy
import json
import pathlib
import sys
import time


MAPPINGS = {
    "account": {"account_firmographics.sub_name": "sub_name"},
    "project": {
        "objectives": "objectives",
        "use_cases": "use_cases",
        "influenced_pipeline_usd": "influenced_pipeline_usd",
    },
    "request_project": {
        "record_links.primary_opportunity_project": "primary_opportunity_link",
    },
    "request": {
        "record_links.tv_request_issue": "tv_request_link",
        "products_in_scope": "products_in_scope",
        "timeline": "timeline",
    },
}
ENRICHMENT_FIELDS = {
    path for group in MAPPINGS.values() for path in group
}


def read_path(value, path):
    for key in path.split("."):
        if not isinstance(value, dict) or key not in value:
            raise ValueError(f"Provider is missing selected enrichment path: {path}")
        value = value[key]
    return value


def matched_record(records, key, expected):
    if not isinstance(records, list) or any(not isinstance(row, dict) for row in records):
        raise ValueError(f"TPSC {key} collection must contain objects")
    matches = [row for row in records if row.get(key) == expected]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one matching TPSC {key}; found {len(matches)}")
    return matches[0]


def has_value(value):
    if isinstance(value, dict):
        return any(has_value(item) for key, item in value.items() if key not in {"source", "note", "derivation"})
    if isinstance(value, list):
        return any(has_value(item) for item in value)
    return value is not None and value != ""


def map_enrichment(kind, provider, payload):
    if kind not in {"request", "opportunity"}:
        raise ValueError("Adapter kind must be request or opportunity")
    if not isinstance(provider, dict) or not isinstance(payload, dict):
        raise ValueError("Provider and TPSC payload must be objects")
    meta = provider.get("meta")
    if not isinstance(meta, dict):
        raise ValueError("Provider meta must be an object")
    if meta.get("schema_version") != "2.1" or meta.get("context_scope") != "anchor_only":
        raise ValueError("Provider must use schema 2.1 and anchor_only scope")
    profile = meta.get("context_profile", "full")
    if profile not in {"full", "widget_enrichment"}:
        raise ValueError("Unsupported provider context_profile")
    ids = meta.get("workfront_ids")
    if not isinstance(ids, dict):
        raise ValueError("Provider native IDs must be an object")
    required_ids = ["program_id", "project_id"]
    if kind == "request":
        required_ids.append("request_id")
    if any(not isinstance(ids.get(key), str) or not ids[key].strip() for key in required_ids):
        raise ValueError("Provider is missing verified native IDs required by this adapter")
    if kind == "opportunity" and ids.get("request_id") is not None:
        raise ValueError("Issue-anchored provider context belongs to the request adapter")

    selected = meta.get("enrichment_fields")
    if selected is not None:
        if not isinstance(selected, list) or any(
            not isinstance(path, str) or path not in ENRICHMENT_FIELDS for path in selected
        ):
            raise ValueError("Invalid provider enrichment_fields")
        selected = set(selected)
    elif profile == "widget_enrichment":
        raise ValueError("Reduced context requires explicit enrichment_fields read evidence")
    else:
        selected = ENRICHMENT_FIELDS

    result = copy.deepcopy(payload)
    account = matched_record(result.get("accounts"), "tpsaccountid", ids["program_id"])
    project = matched_record(result.get("projects"), "tpsprojectid", ids["project_id"])
    if project.get("tpsaccountid") != ids["program_id"]:
        raise ValueError("Primary TPSC project account ID contradicts provider IDs")
    request = None
    if kind == "request":
        request = matched_record(result.get("requests"), "tpsrequestid", ids["request_id"])
        if request.get("tpsprojectid") != ids["project_id"]:
            raise ValueError("Primary TPSC request project ID contradicts provider IDs")
        if request.get("tpsaccountid") != ids["program_id"]:
            raise ValueError("Primary TPSC request account ID contradicts provider IDs")
    elif not isinstance(project.get("requests"), list):
        raise ValueError("Opportunity TPSC project must preserve nested requests")

    applied = []
    skipped = []

    def apply(target, group):
        for source, destination in MAPPINGS[group].items():
            if source not in selected:
                skipped.append(source)
                continue
            value = read_path(provider, source)
            if meta.get("enrichment_fields") is None and not has_value(value):
                skipped.append(source)
                continue
            if source == "influenced_pipeline_usd" and not isinstance(value, dict):
                raise ValueError("influenced_pipeline_usd must be an object")
            if source in {"use_cases", "products_in_scope"} and not isinstance(value, list):
                raise ValueError(f"{source} must be an array")
            if source == "timeline" and not isinstance(value, dict):
                raise ValueError("timeline must be an object")
            target[destination] = copy.deepcopy(value)
            applied.append(source)

    apply(account, "account")
    apply(project, "project")
    if request is not None:
        apply(project, "request_project")
        apply(request, "request")
    return result, {"applied_paths": applied, "skipped_paths": skipped}


def main(argv):
    if len(argv) != 4:
        print("FAIL usage: request|opportunity provider.json data.json output.json", file=sys.stderr)
        return 1
    kind, provider_file, payload_file, output_file = argv
    output = pathlib.Path(output_file)
    inputs = [pathlib.Path(provider_file), pathlib.Path(payload_file)]
    if output.resolve() in {path.resolve() for path in inputs}:
        print("FAIL output must not overwrite either input", file=sys.stderr)
        return 1
    try:
        provider = json.loads(inputs[0].read_text(encoding="utf-8"))
        payload = json.loads(inputs[1].read_text(encoding="utf-8"))
        provider_bytes = inputs[0].stat().st_size
        start = time.perf_counter()
        result, report = map_enrichment(kind, provider, payload)
        elapsed = (time.perf_counter() - start) * 1000
        serialized = json.dumps(result, ensure_ascii=True, separators=(",", ":"))
        output.write_bytes((serialized + "\n").encode("utf-8"))
    except (OSError, ValueError) as error:
        print(f"FAIL {error}", file=sys.stderr)
        return 1
    report.update({
        "mapping_ms": round(elapsed, 3),
        "provider_file_bytes": provider_bytes,
        "widget_data_bytes": len(serialized.encode("utf-8")),
    })
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
