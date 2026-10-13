#!/usr/bin/env python3
"""Poll a Fornax experiment locally and write compact status artifacts."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

TERMINAL_SUCCESS = {"success"}
TERMINAL_FAILURE = {"failed", "terminated", "system_terminated"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--interval", type=int, default=60)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-checks", type=int, default=0, help="0 means unlimited")
    return parser.parse_args()


def fetch(experiment_id: str) -> dict:
    command = [
        "fornax-cli", "experiment", "detail",
        "--experiment-id", experiment_id,
        "--format", "json",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "fornax-cli failed")
    return json.loads(result.stdout)


def snapshot(payload: dict) -> dict:
    experiment = payload.get("experiment") or payload.get("data", {}).get("experiment") or payload
    stats = experiment.get("expt_stats") or {}
    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "experiment_id": str(experiment.get("id") or experiment.get("experiment_id") or ""),
        "status": str(experiment.get("status") or "unknown").lower(),
        "pending": stats.get("pending_turn_count"),
        "processing": stats.get("processing_turn_count"),
        "success": stats.get("success_turn_count"),
        "failed": stats.get("failed_turn_count"),
        "terminated": stats.get("terminated_turn_count"),
    }


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    if args.interval < 10:
        raise SystemExit("--interval must be at least 10 seconds")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    history_path = args.output_dir / "status_history.jsonl"
    last_signature = None
    checks = 0

    while True:
        checks += 1
        try:
            current = snapshot(fetch(args.experiment_id))
        except Exception as exc:  # keep a durable error without losing the watcher
            current = {
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "experiment_id": args.experiment_id,
                "status": "poll_error",
                "error": str(exc),
            }

        write_json(args.output_dir / "latest_status.json", current)
        signature = tuple((key, current.get(key)) for key in sorted(current) if key != "checked_at")
        if signature != last_signature:
            with history_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(current, ensure_ascii=False) + "\n")
            print(json.dumps(current, ensure_ascii=False), flush=True)
            last_signature = signature

        status = current.get("status")
        if status in TERMINAL_SUCCESS | TERMINAL_FAILURE:
            write_json(args.output_dir / "final_status.json", current)
            marker = "EXPERIMENT_DONE" if status in TERMINAL_SUCCESS else "EXPERIMENT_FAILED"
            (args.output_dir / marker).touch()
            return 0 if status in TERMINAL_SUCCESS else 2

        if args.max_checks and checks >= args.max_checks:
            return 3
        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())
