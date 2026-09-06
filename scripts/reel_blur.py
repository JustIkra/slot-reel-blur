"""Build three-copy reel spin textures locally on the original RGBA canvas."""

import argparse
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def motion_blur(source, radius):
    pad = radius + 20
    padded = Image.new("RGBA", (source.width, source.height + pad * 2), (0, 0, 0, 0))
    padded.alpha_composite(source, (0, pad))
    arr = np.asarray(padded, dtype=np.float32) / 255.0
    arr[..., :3] *= arr[..., 3:4]
    kernel = np.ones((radius * 2 + 1, 1), dtype=np.float32)
    kernel /= kernel.sum()
    blurred = np.dstack(
        [
            cv2.filter2D(arr[..., channel], -1, kernel, borderType=cv2.BORDER_CONSTANT)
            for channel in range(4)
        ]
    )
    alpha = blurred[..., 3:4]
    blurred[..., :3] = np.divide(
        blurred[..., :3],
        np.maximum(alpha, 1e-6),
        out=np.zeros_like(blurred[..., :3]),
        where=alpha > 1e-6,
    )
    result = Image.fromarray(np.clip(blurred * 255.0, 0, 255).astype(np.uint8))
    return result.crop((0, pad, source.width, pad + source.height))


def shift_y(image, offset):
    out = Image.new("RGBA", image.size, (0, 0, 0, 0))
    if offset >= 0:
        crop = image.crop((0, 0, image.width, max(0, image.height - offset)))
        out.alpha_composite(crop, (0, offset))
    else:
        crop = image.crop((0, min(image.height, -offset), image.width, image.height))
        out.alpha_composite(crop, (0, 0))
    return out


def crop_safe_offset(image, offset, margin=8):
    bbox = image.getbbox()
    if bbox is None:
        return offset
    _, top, _, bottom = bbox
    if offset < 0:
        return max(offset, min(0, margin - top))
    if offset > 0:
        return min(offset, max(0, image.height - margin - bottom))
    return offset


def multiply_alpha(image, opacity):
    out = image.copy()
    out.putalpha(out.getchannel("A").point(lambda value: round(value * opacity)))
    return out


def blend_core_with_soft_rim(original, blurred, center_blur=0.30):
    bbox = original.getbbox()
    if bbox is None:
        return Image.blend(original, blurred, center_blur)
    _, top, _, bottom = bbox
    height, width = original.height, original.width
    feather = min(136, max(1, (bottom - top) // 2))
    vertical_weights = np.full(height, center_blur, dtype=np.float32)
    vertical_weights[top : top + feather] = np.linspace(
        1.0, center_blur, feather, dtype=np.float32
    )
    vertical_weights[bottom - feather : bottom] = np.linspace(
        center_blur, 1.0, feather, dtype=np.float32
    )
    alpha = np.asarray(original.getchannel("A"), dtype=np.uint8)
    inside = (alpha > 8).astype(np.uint8)
    distance = cv2.distanceTransform(inside, cv2.DIST_L2, 3)
    edge_width = max(28, min(56, (bottom - top) // 7))
    edge_weights = 1.0 - np.clip(distance / edge_width, 0.0, 1.0) * (1.0 - center_blur)
    edge_weights = np.where(inside > 0, edge_weights, center_blur)
    original_arr = np.asarray(original, dtype=np.float32)
    blurred_arr = np.asarray(blurred, dtype=np.float32)
    weights = np.maximum(vertical_weights[:, None], edge_weights).reshape(
        height, width, 1
    )
    out = original_arr.copy()
    out[..., :3] = (
        original_arr[..., :3] * (1.0 - weights) + blurred_arr[..., :3] * weights
    )
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def make_symbol(source, radius=20, offset=20):
    if radius < 0 or offset < 0:
        raise ValueError("radius and offset must be nonnegative")
    source = source.convert("RGBA")
    blurred = motion_blur(source, radius)
    core = multiply_alpha(blend_core_with_soft_rim(source, blurred), 0.90)
    top = multiply_alpha(shift_y(blurred, crop_safe_offset(blurred, -offset)), 0.60)
    bottom = multiply_alpha(shift_y(blurred, crop_safe_offset(blurred, offset)), 0.60)
    out = Image.new("RGBA", source.size, (0, 0, 0, 0))
    for layer in (top, core, bottom):
        out.alpha_composite(layer)
    return out


def build_set(source_dir, output_dir, abydos_names=False, radius=20, offset=20):
    sources = sorted(source_dir.glob("*.png"))
    if not sources:
        raise ValueError("No source PNGs")
    mapping = (
        {"high_symbol1.png": "high1.png", "high_symbol2.png": "high2.png"}
        if abydos_names
        else {}
    )
    names = [mapping.get(path.name, path.name) for path in sources]
    if len(set(names)) != len(names):
        raise ValueError("Source names collide after mapping")
    if output_dir.resolve() == source_dir.resolve():
        raise ValueError("Source and output directories must differ")
    if output_dir.exists():
        raise FileExistsError(f"Use a new candidate directory: {output_dir}")
    if radius < 0 or offset < 0:
        raise ValueError("radius and offset must be nonnegative")
    for source in sources:
        with Image.open(source) as image:
            image.load()
    output_dir.mkdir(parents=True)
    report = {
        "recipe": "abydos-three-copy",
        "radius": radius,
        "offset": offset,
        "layer_order": ["top", "core", "bottom"],
        "outputs": [],
    }
    for source, name in zip(sources, names):
        with Image.open(source) as image:
            result = make_symbol(image, radius, offset)
        result.save(output_dir / name)
        report["outputs"].append(
            {"source": source.name, "file": name, "size": list(result.size)}
        )
    (output_dir / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument(
        "--output-dir", type=Path, required=True, help="New candidate directory"
    )
    parser.add_argument(
        "--abydos-names", action="store_true", help="Map high_symbol1/2 to high1/2"
    )
    parser.add_argument(
        "--radius", type=int, default=20, help="Vertical box radius in source pixels"
    )
    parser.add_argument(
        "--offset", type=int, default=20, help="Trail displacement in source pixels"
    )
    args = parser.parse_args()
    report = build_set(
        args.source_dir, args.output_dir, args.abydos_names, args.radius, args.offset
    )
    print(json.dumps({"count": len(report["outputs"]), "output": str(args.output_dir)}))


if __name__ == "__main__":
    main()
