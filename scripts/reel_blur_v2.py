"""Approximate the reference game's blur with a continuous premultiplied filter."""

import argparse
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


@dataclass(frozen=True)
class Settings:
    scale_x: float = 1.0
    scale_y: float = 1.0
    motion_length: float = 30.0
    softness: float = 0.0
    core_mix: float = 0.0
    shift_x: float = 0.0
    shift_y: float = 0.0

    def __post_init__(self):
        if not all(math.isfinite(value) for value in asdict(self).values()):
            raise ValueError("Settings must be finite numbers")
        if self.scale_x <= 0 or self.scale_y <= 0:
            raise ValueError("Scales must be positive")
        if self.motion_length < 0 or self.softness < 0:
            raise ValueError("Motion length and softness must be nonnegative")
        if not 0 <= self.core_mix <= 1:
            raise ValueError("Core mix must be between 0 and 1")


PRESETS = {
    "coins": Settings(),
    "symbols": Settings(scale_x=0.8, scale_y=1.2, motion_length=40, softness=4),
    "soft-symbols": Settings(scale_x=0.8, scale_y=1.2, motion_length=40, softness=6),
}


def motion_kernel(length):
    if length <= 1:
        return np.ones(1, dtype=np.float64)
    radius = math.ceil(length / 2)
    positions = np.arange(-radius, radius + 1, dtype=np.float64)
    weights = np.clip(length / 2 + 0.5 - np.abs(positions), 0, 1)
    return weights / weights.sum()


def make_symbol(source, settings=None):
    settings = Settings() if settings is None else settings
    pixels = np.asarray(source.convert("RGBA"), dtype=np.float64) / 255
    pixels[..., :3] *= pixels[..., 3:4]
    height, width = pixels.shape[:2]
    transform = np.array(
        [
            [
                settings.scale_x,
                0,
                (width - 1) * (1 - settings.scale_x) / 2 + settings.shift_x,
            ],
            [
                0,
                settings.scale_y,
                (height - 1) * (1 - settings.scale_y) / 2 + settings.shift_y,
            ],
        ],
        dtype=np.float64,
    )
    base = cv2.warpAffine(
        pixels,
        transform,
        (width, height),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
    )
    core = base
    if settings.softness > 0:
        radius = math.ceil(settings.softness * 4)
        positions = np.arange(-radius, radius + 1, dtype=np.float64)
        smooth = np.exp(-0.5 * (positions / settings.softness) ** 2)
        smooth /= smooth.sum()
        base = cv2.sepFilter2D(base, -1, smooth, smooth, borderType=cv2.BORDER_CONSTANT)
    moved = cv2.sepFilter2D(
        base,
        -1,
        np.ones(1),
        motion_kernel(settings.motion_length),
        borderType=cv2.BORDER_CONSTANT,
    )
    result = moved * (1 - settings.core_mix) + core * settings.core_mix
    alpha = result[..., 3:4]
    color = np.divide(
        result[..., :3],
        alpha,
        out=np.zeros_like(result[..., :3]),
        where=alpha > 1e-10,
    )
    rgba = np.rint(np.clip(np.concatenate((color, alpha), axis=2), 0, 1) * 255).astype(
        np.uint8
    )
    rgba[rgba[..., 3] == 0, :3] = 0
    return Image.fromarray(rgba)


def resolve_settings(preset, overrides):
    options = dict(overrides)
    name = options.pop("preset", preset)
    if name not in PRESETS:
        raise ValueError(f"Unknown preset: {name}")
    try:
        return Settings(**(asdict(PRESETS[name]) | options))
    except TypeError as error:
        raise ValueError(f"Invalid settings: {error}") from error


def build_set(source_dir, output_dir, preset="symbols", profile=None):
    source_dir, output_dir = Path(source_dir), Path(output_dir)
    if source_dir.resolve() == output_dir.resolve():
        raise ValueError("Source and output directories must differ")
    if output_dir.exists():
        raise FileExistsError(f"Refusing existing output directory: {output_dir}")
    sources = sorted(source_dir.glob("*.png"))
    if not sources:
        raise ValueError("No source PNGs")
    profile = {} if profile is None else profile
    if set(profile) - {"defaults", "files"}:
        raise ValueError("Profile supports only 'defaults' and 'files'")
    defaults = profile.get("defaults", {})
    files = profile.get("files", {})
    unknown = set(files) - {source.name for source in sources}
    if unknown:
        raise ValueError(f"Profile contains missing source files: {sorted(unknown)}")
    settings = {
        source.name: resolve_settings(preset, defaults | files.get(source.name, {}))
        for source in sources
    }
    for source in sources:
        with Image.open(source) as image:
            image.load()
    output_dir.mkdir(parents=True)
    report = {"recipe": "game-reference-v2", "preset": preset, "outputs": []}
    for source in sources:
        with Image.open(source) as image:
            result = make_symbol(image, settings[source.name])
        result.save(output_dir / source.name)
        bounds = result.getbbox()
        touches_edge = bounds is not None and (
            bounds[0] == 0
            or bounds[1] == 0
            or bounds[2] == result.width
            or bounds[3] == result.height
        )
        report["outputs"].append(
            {
                "file": source.name,
                "size": list(result.size),
                "settings": asdict(settings[source.name]),
                "alpha_touches_edge": touches_edge,
            }
        )
    (output_dir / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--preset", choices=tuple(PRESETS), default="symbols")
    parser.add_argument(
        "--profile", type=Path, help="JSON defaults and per-filename settings"
    )
    args = parser.parse_args()
    try:
        profile = json.loads(args.profile.read_text()) if args.profile else None
        report = build_set(args.source_dir, args.output_dir, args.preset, profile)
    except (ValueError, OSError) as error:
        parser.exit(2, f"{error}\n")
    print(json.dumps({"count": len(report["outputs"]), "output": str(args.output_dir)}))


if __name__ == "__main__":
    main()
