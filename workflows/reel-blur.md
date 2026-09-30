# Reel spin blur — final three-copy recipe

Use for the static IMAGE texture displayed while reels move, not for blurring the
whole canvas, paytable or a Spine animation. Produce it deterministically from the
accepted full static symbol: no new AI art is required for this derivative.

The supported recipe is the final Book of Abydos three-copy stack. Do not substitute
Gaussian blur, a single smeared sprite, or the earlier ghost-stack experiments.

## Source and registration

Use a complete RGBA render of the symbol, including frame/letter/character and any
parts visible in its static state. A cutout rig's background-only base is not a full
symbol. When a static render must be obtained from Spine, use slot-spine-skin for that
step, then return here with the registered RGBA source.

Keep source canvas dimensions, aspect ratio and center unchanged. The validated Abydos
inputs are 400x400 paytable renders, but this is not a universal paytable-to-reel scale.
Read the current symbol catalog and blur template to obtain actual asset keys and scale.
Ensure transparent vertical breathing room around the subject. The filter pads internally
then returns the original canvas; full-bleed inputs can still truncate the motion tail.
Inspect top/bottom edges rather than silently shrinking or trimming the symbol to hide it.

## Command

From the slot-reel-blur repository with its requirements installed:

```bash
python scripts/reel_blur.py \
  --source-dir /path/to/game/.tmp/YYYY-MM-DD/reel-blur/RUN_ID/static-symbols \
  --output-dir /path/to/game/.tmp/YYYY-MM-DD/reel-blur/RUN_ID/candidate-v1
```

The source directory should contain only intended PNG symbols. The output directory
must be new; the script refuses overwrites and source/output equality. It emits one
same-size RGBA PNG per input plus `manifest.json`. It neither packs nor integrates assets.

For Abydos paytable input add `--abydos-names`:

| Static input | Blur output |
|---|---|
| high_symbol1.png | high1.png |
| high_symbol2.png | high2.png |
| head5–8, scatter, tail, wild, wing1–3 | Same filename |

The switch only maps names; it does not assert all 12 symbols were supplied. Verify the
manifest against the target game's symbol catalog. Colliding mapped names are rejected.

## Exact stack

1. Premultiply RGB by alpha, apply a vertical normalized box kernel of radius 20
   (41x1 samples), then unpremultiply. Transparent pixels cannot bleed hidden RGB
   into the filtered edge. No horizontal convolution or Gaussian pass.
2. Build a recognizable core: blend 30% filtered RGB into original RGB in the center;
   increase to full filtered RGB near top/bottom and silhouette edges. Preserve the
   original core alpha, then multiply it by 0.90.
3. Build two copies of the filtered symbol at requested offsets -20 and +20 source
   pixels, each with alpha multiplied by 0.60. Clamp offsets to available transparent
   space with an 8-pixel margin; do not wrap pixels across the opposite edge.
4. Composite in this exact order: **top trail → core → bottom trail**. The asymmetric
   over-compositing order is part of the approved result. Save without crop or resize.

The defaults reproduce the final 400x400 Abydos outputs. `--radius` and `--offset` are
explicit source-pixel parameters for a newly reviewed candidate, not automatic speed
controls. Edge-softening constants also come from that source scale; do not assume
doubling only these two arguments gives an equivalent recipe on an 800x800 source.

## Verification and handoff

Compare source / candidate / accepted reference on dark reel color and checkerboard,
at actual display size. Check recognizable symbol, saturated material, gentle vertical
motion, readable core, no dark fringe, cut tails, hard stripes or horizontal widening.
Verify pixel dimensions and file-to-key mapping across the entire set. Do not infer
correct scale from filenames or from a paytable screenshot.

When integration is requested, promote only approved PNGs to the existing blur source
paths, preserve template keys, and rebuild the game's texture atlases (`assets:textures`
or its configured equivalent). Replacing raw PNGs alone does not update packed runtime
assets. Use zephyr-launcher-session for real-wrapper reel review; test the transition
between blur and landed symbols for scale/center jumps. Asset-only work stops at handoff.

## Provenance

The original derivation is retained in the workspace artifact index under the paytable Spine materials.
Despite its historical name, its final radius is **20**, not 8. All 12 extracted outputs
were compared as decoded RGBA against the blur assets in Book of Abydos commit
`697dbf6`; they matched exactly. Older developer notes describe a different, rejected
recipe and are not the source of this workflow. No temporary game scripts are needed
to execute the skill's implementation.
