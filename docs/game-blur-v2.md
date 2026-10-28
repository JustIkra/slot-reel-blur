# Game-reference blur v2

[reel_blur_v2.py](../scripts/reel_blur_v2.py) is an additional approximation of the
blur in the supplied game atlas. The existing `reel_blur.py` recipe remains unchanged.
This version uses the same Pillow, NumPy and OpenCV dependencies.

## Generate

Supply complete upright RGBA PNG symbols. Leave transparent space above and below
each symbol. The script keeps the canvas dimensions and filters around its center.
It rejects an existing output directory.

```bash
python3 scripts/reel_blur_v2.py \
  --source-dir /path/to/symbols \
  --output-dir /path/to/new-candidate \
  --preset symbols
```

| Preset | Scale X / Y | Vertical motion length | Softness sigma |
| --- | --- | --- | --- |
| `coins` | 1.0 / 1.0 | 30 | 0 |
| `symbols` | 0.8 / 1.2 | 40 | 4 |
| `soft-symbols` | 0.8 / 1.2 | 40 | 6 |

Motion length and softness use source pixels. These values were estimated from
symbols roughly 100–250 pixels across. They do not automatically scale to a new
resolution. The geometric squeeze and stretch are intentional parts of this recipe.

The filter premultiplies RGB by alpha, applies the spatial transform, softens the
result and convolves it with one centered vertical box kernel. `core_mix` blends a
fraction of the sharp, transformed symbol back into the motion result. The output
is converted back to straight-alpha RGBA. Filtering uses transparent borders and
does not wrap pixels. The manifest lists the effective settings and reports outputs
whose visible alpha reaches a canvas edge. Inspect these outputs for clipped tails.

## Calibrate individual files

Pass `--profile /path/to/profile.json` to apply defaults or filename-specific values:

```json
{
  "defaults": {"preset": "symbols"},
  "files": {
    "grand.png": {"preset": "coins"},
    "green.png": {"preset": "soft-symbols"},
    "seven.png": {"core_mix": 0.25, "motion_length": 30}
  }
}
```

Supported fields are `preset`, `scale_x`, `scale_y`, `motion_length`, `softness`,
`core_mix`, `shift_x` and `shift_y`. `core_mix` ranges from 0 to 1. Shift values use
source pixels. Precedence is: command-line preset, profile defaults, file overrides.
Filename entries must match supplied PNGs. Profiles store filter parameters only.

The fitted [atlas profile](../examples/game-blur-v2/atlas-profile.json) uses the
15 extracted filenames from the supplied atlas. Use it with the upright source PNGs
from this comparison, or edit the filename keys and recalibrate for other artwork.

The game atlas has rotated entries. Restore each static symbol and reference to the
same upright orientation before calibration. In the supplied atlas, the ringed
sphere's static image and the X symbol's blur required additional rotation.

This is a reconstruction from rendered reference images. Calibration error on the
same images measures resemblance; it does not establish the original game's source
code or behavior on unseen artwork. Compare the full catalog on dark and checkerboard
backgrounds before acceptance. Runtime integration requires a separate game check.

## Checks

```bash
python3 -m unittest discover -s tests
```
