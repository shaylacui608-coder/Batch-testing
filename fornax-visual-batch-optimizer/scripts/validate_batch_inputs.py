#!/usr/bin/env python3
"""Validate durable source rows or official Fornax multi_part eval items."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--stage", choices=("source", "official"), required=True)
    parser.add_argument("--expected-count", type=int, default=60)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def load_rows(path: Path) -> list[dict]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open(newline="", encoding="utf-8-sig") as handle:
            return list(csv.DictReader(handle))
    if suffix in {".jsonl", ".ndjson"}:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    for key in ("items", "rows", "data"):
        if isinstance(payload.get(key), list):
            return payload[key]
    raise ValueError("JSON must be an array or contain items/rows/data array")


def flatten_official(item: dict) -> dict:
    turns = item.get("turns") or []
    fields = (turns[0].get("field_datas") if turns else None) or item.get("field_datas") or []
    flattened: dict[str, object] = {}
    for field in fields:
        name = field.get("name") or field.get("key")
        content = field.get("content") or {}
        if not name:
            continue
        flattened[name] = content.get("text") if content.get("content_type") == "text" else content
    return flattened


def nonempty(value: object) -> bool:
    return value is not None and str(value).strip() != ""


def valid_multipart(value: object) -> bool:
    if not isinstance(value, dict) or value.get("content_type") != "multi_part":
        return False
    parts = value.get("multi_part") or []
    return any(
        part.get("content_type") == "image"
        and nonempty((part.get("image") or {}).get("url"))
        for part in parts if isinstance(part, dict)
    )


def validate(rows: list[dict], stage: str, expected: int) -> dict:
    errors: list[dict] = []
    warnings: list[dict] = []
    seen: set[str] = set()
    normalized = [flatten_official(row) if stage == "official" else row for row in rows]

    if len(normalized) != expected:
        errors.append({"code": "wrong_row_count", "expected": expected, "actual": len(normalized)})

    for index, row in enumerate(normalized, start=1):
        case_id = str(row.get("case_id") or "").strip()
        if not case_id:
            errors.append({"row": index, "code": "missing_case_id"})
        elif case_id in seen:
            errors.append({"row": index, "case_id": case_id, "code": "duplicate_case_id"})
        seen.add(case_id)

        if stage == "source":
            for field in ("merchant_name", "main_title", "category", "layout_variant", "source_image_uri_1"):
                if not nonempty(row.get(field)):
                    errors.append({"row": index, "case_id": case_id, "code": "missing_field", "field": field})
            uri1 = str(row.get("source_image_uri_1") or "").strip()
            uri2 = str(row.get("source_image_uri_2") or "").strip()
            if uri2 and uri1 == uri2:
                errors.append({"row": index, "case_id": case_id, "code": "duplicate_image_uris"})
            if not row.get("must_show_text"):
                warnings.append({"row": index, "case_id": case_id, "code": "empty_must_show_text"})
        else:
            if not valid_multipart(row.get("image_ref_1")):
                errors.append({"row": index, "case_id": case_id, "code": "invalid_image_ref_1"})
            if nonempty(row.get("source_image_uri_2")) and not valid_multipart(row.get("image_ref_2")):
                errors.append({"row": index, "case_id": case_id, "code": "missing_image_ref_2_for_two_image_row"})
            url1 = str(row.get("source_image_url_1") or "").strip()
            url2 = str(row.get("source_image_url_2") or "").strip()
            if url2 and url1 == url2:
                errors.append({"row": index, "case_id": case_id, "code": "duplicate_runtime_image_urls"})

    return {
        "stage": stage,
        "expected_count": expected,
        "actual_count": len(normalized),
        "unique_case_count": len(seen),
        "passed": not errors,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    args = parse_args()
    report = validate(load_rows(args.input), args.stage, args.expected_count)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    sys.exit(main())
