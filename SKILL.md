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
If the user has not specified a recipe, build separate **V1** (approved top-trail → core → bottom-trail)
and **V2** ([continuous game-reference blur](docs/game-blur-v2.md)) candidates.
Show a labelled **original / V1 / V2** contact sheet before asking the user to choose.
The user may select one version for the whole set or different versions per symbol.
Do not choose a winner from fitting scores or silently replace V1 with V2. If the user
already specified a version, generate only that version unless they also request a
comparison. Keep the original V1 script intact.
Preserve source files, output canvas and asset keys; V2's explicit scale transform
changes the artwork proportions inside that canvas. Keep candidates in the
game's ignored `.tmp/YYYY-MM-DD/<task>/<run>/`. Use the run's start date in
`Europe/Moscow` and a unique run ID; resume in the same directory. Preserve historical
`.tmp_*` artifacts and leave accepted assets unchanged until approved.

## Run

Use Python 3.10+ with `requirements.txt` installed in the chosen environment.
The shared workspace already provides the prepared interpreter listed in the workspace tools index.
No `slot-gen` installation is required. From this skill's directory:

```bash
python scripts/compare_reel_blur.py \
  --source-dir /path/to/game/.tmp/YYYY-MM-DD/reel-blur/RUN_ID/static-symbols \
  --output-dir /path/to/game/.tmp/YYYY-MM-DD/reel-blur/RUN_ID/comparison
```

This generates `v1/`, `v2/`, paginated dark/checkerboard contact sheets and an undecided
`selection.json`. Show every page. Record the user's choices as `v1` or `v2` per file;
leave unselected files undecided. See [comparison and selection](docs/compare-blur.md).
Choose V2 presets from the current catalog; use `--v2-profile` for mixed symbol families.
The bundled atlas calibration profile applies only to its corresponding extracted art.

The separate `reel_blur.py` and `reel_blur_v2.py` entry points remain available for an
explicit version choice. V1's `--help` includes radius/offset and Abydos filename mapping.
All generation commands refuse an existing output directory.

Verify the whole symbol catalog, alpha edges and actual display scale. Asset delivery
does not authorize game integration. If the input must first be rendered from a rig,
use `slot-spine-skin` for that step only. If in-game verification is requested, use
`zephyr-launcher-session` after the target game's normal texture build.

Tests: `python -m unittest discover -s tests`.
