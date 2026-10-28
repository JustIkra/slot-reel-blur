"""Build V1/V2 blur candidates and contact sheets for user selection."""

import argparse
import importlib.util
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def load_recipe(name):
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).with_name(name + ".py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def font(size):
    for name in (
        "DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
    ):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def contact_sheet(source_dir, output_dir, names, page, checker=False):
    cell, card_width, row_height = 256, 804, 324
    rows = (len(names) + 1) // 2
    sheet = Image.new("RGB", (1624, 82 + rows * row_height), "#111520")
    draw = ImageDraw.Draw(sheet)
    title = "Original / V1 / V2 - choose one per symbol or for the whole set"
    draw.text((20, 14), title, font=font(24), fill="#f2f4fa")
    draw.text(
        (20, 48),
        f"Page {page} | V1: three-copy | V2: continuous motion",
        font=font(18),
        fill="#abb9ce",
    )
    for i, name in enumerate(names):
        x, y = 12 + (i % 2) * card_width, 82 + (i // 2) * row_height
        label = ImageDraw.Draw(sheet)
        label.text((x + 8, y), name, font=font(19), fill="#f2f4fa")
        for j, (folder, heading) in enumerate(
            (
                (source_dir, "ORIGINAL"),
                (output_dir / "v1", "V1"),
                (output_dir / "v2", "V2"),
            )
        ):
            left, top = x + j * (cell + 10), y + 30
            draw.text(
                (left + 8, top),
                heading,
                font=font(17),
                fill="#7de3d0" if j else "#b8c2d5",
            )
            tile = Image.new("RGBA", (cell, cell), "#242936")
            if checker:
                grid = ImageDraw.Draw(tile)
                for gy in range(0, cell, 16):
                    for gx in range(0, cell, 16):
                        if (gx // 16 + gy // 16) % 2:
                            grid.rectangle((gx, gy, gx + 15, gy + 15), fill="#3b4251")
            with Image.open(folder / name) as image:
                sprite = image.convert("RGBA")
            sprite.thumbnail((cell, cell), Image.Resampling.LANCZOS)
            tile.alpha_composite(
                sprite, ((cell - sprite.width) // 2, (cell - sprite.height) // 2)
            )
            sheet.paste(tile.convert("RGB"), (left, top + 24))
    filename = f"contact-{'checker-' if checker else ''}{page:02d}.png"
    sheet.save(output_dir / filename)
    return filename


def build_comparison(source_dir, output_dir, v2_preset="symbols", profile=None):
    source_dir, output_dir = Path(source_dir), Path(output_dir)
    if output_dir.exists():
        raise FileExistsError(f"Refusing existing output directory: {output_dir}")
    v1, v2 = load_recipe("reel_blur"), load_recipe("reel_blur_v2")
    v2_report = v2.build_set(
        source_dir, output_dir / "v2", preset=v2_preset, profile=profile
    )
    v1.build_set(source_dir, output_dir / "v1")
    names = [item["file"] for item in v2_report["outputs"]]
    report = {
        "source_dir": str(source_dir.resolve()),
        "symbols": names,
        "contact_sheets": [],
        "checker_sheets": [],
        "selection": "selection.json",
    }
    for offset in range(0, len(names), 6):
        page = offset // 6 + 1
        subset = names[offset : offset + 6]
        report["contact_sheets"].append(
            contact_sheet(source_dir, output_dir, subset, page)
        )
        report["checker_sheets"].append(
            contact_sheet(source_dir, output_dir, subset, page, checker=True)
        )
    (output_dir / "selection.json").write_text(
        json.dumps(dict.fromkeys(names), indent=2) + "\n"
    )
    (output_dir / "comparison.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--v2-preset", choices=("coins", "symbols", "soft-symbols"), default="symbols"
    )
    parser.add_argument("--v2-profile", type=Path)
    args = parser.parse_args()
    try:
        profile = json.loads(args.v2_profile.read_text()) if args.v2_profile else None
        report = build_comparison(
            args.source_dir, args.output_dir, args.v2_preset, profile
        )
    except (ValueError, OSError) as error:
        parser.exit(2, f"{error}\n")
    print(
        json.dumps(
            {
                "count": len(report["symbols"]),
                "output": str(args.output_dir),
                "contact_sheets": report["contact_sheets"],
            }
        )
    )


if __name__ == "__main__":
    main()
