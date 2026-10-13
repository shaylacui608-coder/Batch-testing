#!/usr/bin/env python3
"""Build contact sheets and input/output comparisons from local images.

Manifest format: JSON array with case_id, output_path and optional input_paths list.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--per-sheet", type=int, default=10)
    return parser.parse_args()


def local_path(value: str, base: Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (base / path).resolve()


def fit_image(path: Path, size: tuple[int, int]) -> Image.Image:
    with Image.open(path) as image:
        return ImageOps.contain(image.convert("RGB"), size, Image.Resampling.LANCZOS)


def paste_center(canvas: Image.Image, image: Image.Image, box: tuple[int, int, int, int]) -> None:
    left, top, right, bottom = box
    x = left + (right - left - image.width) // 2
    y = top + (bottom - top - image.height) // 2
    canvas.paste(image, (x, y))


def contact_sheet(rows: list[dict], output: Path, base: Path) -> None:
    columns, cell_w, cell_h, label_h = 2, 800, 260, 34
    grid_rows = math.ceil(len(rows) / columns)
    canvas = Image.new("RGB", (columns * cell_w, grid_rows * (cell_h + label_h)), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    for index, row in enumerate(rows):
        col, grid_row = index % columns, index // columns
        x, y = col * cell_w, grid_row * (cell_h + label_h)
        image = fit_image(local_path(row["output_path"], base), (cell_w - 20, cell_h - 20))
        paste_center(canvas, image, (x + 10, y + 10, x + cell_w - 10, y + cell_h - 10))
        draw.text((x + 12, y + cell_h + 8), str(row.get("case_id", index + 1)), fill="black", font=font)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, quality=90)


def comparison(row: dict, output: Path, base: Path) -> None:
    panel_w, panel_h, label_h = 700, 420, 36
    inputs = row.get("input_paths") or []
    paths = [local_path(value, base) for value in inputs] + [local_path(row["output_path"], base)]
    labels = [f"INPUT {i + 1}" for i in range(len(inputs))] + ["OUTPUT"]
    canvas = Image.new("RGB", (panel_w * len(paths), panel_h + label_h), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    for index, (path, label) in enumerate(zip(paths, labels)):
        image = fit_image(path, (panel_w - 24, panel_h - 24))
        paste_center(canvas, image, (index * panel_w + 12, 12, (index + 1) * panel_w - 12, panel_h - 12))
        draw.text((index * panel_w + 12, panel_h + 10), label, fill="black", font=font)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, quality=90)


def main() -> int:
    args = parse_args()
    rows = json.loads(args.manifest.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not rows:
        raise SystemExit("manifest must be a non-empty JSON array")
    base = args.manifest.parent
    missing = []
    for row in rows:
        for value in (row.get("input_paths") or []) + [row.get("output_path")]:
            if not value or not local_path(value, base).is_file():
                missing.append({"case_id": row.get("case_id"), "path": value})
    if missing:
        print(json.dumps({"error": "missing_files", "files": missing}, ensure_ascii=False, indent=2))
        return 2

    sheets = args.output_dir / "contact_sheets"
    comparisons = args.output_dir / "comparisons"
    for start in range(0, len(rows), args.per_sheet):
        number = start // args.per_sheet + 1
        contact_sheet(rows[start:start + args.per_sheet], sheets / f"contact_{number:02d}.jpg", base)
    for index, row in enumerate(rows, start=1):
        safe_id = "".join(char if char.isalnum() or char in "-_" else "_" for char in str(row.get("case_id") or index))
        comparison(row, comparisons / f"{safe_id}.jpg", base)
    print(json.dumps({"rows": len(rows), "sheets": math.ceil(len(rows) / args.per_sheet), "output_dir": str(args.output_dir)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
