# Slot reel blur tools

Build spin-blur textures from existing static symbols using the established three-copy motion recipe. This is a deterministic image-processing tool; it does not generate new source artwork.

## Setup

Use Python 3.10+ and install the repository requirements in a virtual environment. Load the slot-reel-blur skill for the recipe and CLI options.

## Verification

```bash
python -m unittest discover -s tests
```

Inspect the result with the source symbol at the intended in-game scale before integration.

## Working files

Use the target project's `.tmp/YYYY-MM-DD/<task>/<run>/` with a Europe/Moscow start date. Keep accepted sources in their indexed asset locations. Caches, credentials and local memory remain outside Git.
