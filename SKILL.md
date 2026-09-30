---
name: slot-reel-blur
description: >
  Use when preparing or rebuilding reel spin-blur textures from existing static slot
  symbol images, including the approved three-copy motion recipe. Not for generating
  new artwork, promo composition, whole-screen blur or Spine rigging.
---

# Reel blur from source symbols

Turn complete static RGBA symbols into registered spin textures. This is a local,
deterministic asset-processing skill: no generator, provider package or API keys.

Read the target game's `.memory-base/index.md` and symbol mapping when present, then
read [the three-copy workflow](workflows/reel-blur.md) before processing images.
Use the last approved top-trail → core → bottom-trail recipe, not Gaussian blur.
Preserve source canvas, center, aspect ratio and asset keys; keep candidates in the
game's ignored `.tmp/YYYY-MM-DD/<task>/<run>/`. Use the run's start date in
`Europe/Moscow` and a unique run ID; resume in the same directory. Preserve historical
`.tmp_*` artifacts and leave accepted assets unchanged until approved.

## Run

Use Python 3.10+ with `requirements.txt` installed in the chosen environment.
The shared workspace already provides the prepared interpreter listed in the workspace tools index.
No `slot-gen` installation is required. From this skill's directory:

```bash
python scripts/reel_blur.py \
  --source-dir /path/to/game/.tmp/YYYY-MM-DD/reel-blur/RUN_ID/static-symbols \
  --output-dir /path/to/game/.tmp/YYYY-MM-DD/reel-blur/RUN_ID/candidate-v1
```

Use `--help` for the explicit radius/offset and Abydos filename mapping options.
The script outputs PNGs plus a manifest and refuses an existing output directory.

Verify the whole symbol catalog, alpha edges and actual display scale. Asset delivery
does not authorize game integration. If the input must first be rendered from a rig,
use `slot-spine-skin` for that step only. If in-game verification is requested, use
`zephyr-launcher-session` after the target game's normal texture build.

Tests: `python -m unittest discover -s tests`.
