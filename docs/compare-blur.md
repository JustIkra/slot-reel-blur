# Compare and choose reel blur

When the user has not specified a recipe, present the original, V1 and V2 together. The user can choose one
recipe for the catalog or choose a different recipe for each symbol. Keep both versions
available. If the user specifies a version, generate only that version unless they
also request a comparison. Direct V1 generation is documented in the
[three-copy workflow](../workflows/reel-blur.md); direct V2 generation is documented
in the [V2 guide](game-blur-v2.md).

## Build the comparison

Use complete upright RGBA PNGs with registered canvases and asset filenames:

```bash
python3 scripts/compare_reel_blur.py \
  --source-dir /path/to/static-symbols \
  --output-dir /path/to/new-comparison \
  --v2-preset symbols
```

The output directory must be new. It contains:

- `v1/`: the existing three-copy recipe and its manifest.
- `v2/`: the [V2 recipe](game-blur-v2.md) and its manifest.
- `contact-01.png`, `contact-02.png`, etc.: original / V1 / V2 on a dark background.
- `contact-checker-01.png`, etc.: matching pages for alpha inspection.
- `comparison.json`: catalog, source directory and sheet paths.
- `selection.json`: a filename-to-choice map, initially `null` for every symbol.

Each page contains at most six symbols. Show every page. All three images in a card
use the same display scale. Native PNGs retain the source canvas dimensions. Contact
sheet thumbnails do not establish runtime scale or moving-reel behavior.

For circular symbols use `--v2-preset coins`. Use `--v2-preset soft-symbols` for the
softer variant. For a mixed catalog, pass `--v2-profile /path/to/profile.json` with
filename-specific presets and settings. The bundled atlas profile was fitted to the
original comparison art; do not apply it automatically to another game's catalog.

## Record the choice

Ask for a choice after the user has seen the sheets. Accept a catalog-wide choice,
such as "V2 for everything", or per-symbol choices, such as "V1 for BAR, V2 for the
gems". Record only explicit choices in the run's `selection.json`:

```json
{
  "bar.png": "v1",
  "green.png": "v2",
  "wild.png": null
}
```

An undecided symbol keeps `null`. Do not infer acceptance from a low fitting error or
from the existence of a candidate. Keep the two candidate directories and the source
PNGs intact. A chosen set can be assembled from the corresponding version directories
when requested. Selecting a visual version does not by itself request game integration.

The comparison command keeps input filenames in both variants. If the game's asset
keys differ from render filenames, apply the game's existing mapping when assembling
the chosen set. V1's direct CLI retains its `--abydos-names` option.
