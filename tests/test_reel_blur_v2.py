import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from test_reel_blur import load_script


class GameBlurV2Tests(unittest.TestCase):
    def test_filter_does_not_leak_hidden_rgb_or_wrap_motion(self):
        blur = load_script("reel_blur_v2")
        pixels = np.zeros((121, 101, 4), dtype=np.uint8)
        pixels[..., 2] = 255
        pixels[3:15, 44:57] = (255, 90, 0, 255)
        source = Image.fromarray(pixels)
        result = np.asarray(
            blur.make_symbol(source, blur.Settings(motion_length=30, softness=2))
        )
        visible = result[..., 3] > 0
        self.assertEqual(result[..., 2][visible].max(), 0)
        self.assertGreater(result[20, 50, 3], 0)
        self.assertEqual(result[-1, :, 3].max(), 0)
        self.assertTrue(np.array_equal(np.asarray(source), pixels))

    def test_motion_is_centered_and_preserves_canvas(self):
        blur = load_script("reel_blur_v2")
        pixels = np.zeros((161, 161, 4), dtype=np.uint8)
        pixels[70:91, 70:91] = (255, 200, 0, 255)
        result = blur.make_symbol(Image.fromarray(pixels), blur.Settings())
        alpha = np.asarray(result)[..., 3]
        self.assertEqual(result.mode, "RGBA")
        self.assertEqual(result.size, (161, 161))
        self.assertTrue(np.array_equal(alpha, alpha[::-1]))
        self.assertTrue(np.array_equal(alpha, alpha[:, ::-1]))
        self.assertGreater(int(alpha[60, 80]), 0)
        self.assertEqual(int(alpha[80, 60]), 0)

    def test_symbol_preset_squeezes_width_and_stretches_height(self):
        blur = load_script("reel_blur_v2")
        source = Image.new("RGBA", (201, 201))
        pixels = np.asarray(source).copy()
        pixels[60:141, 50:151] = (255, 160, 20, 255)
        settings = blur.Settings(scale_x=0.8, scale_y=1.2, motion_length=0)
        out = blur.make_symbol(Image.fromarray(pixels), settings)
        left, top, right, bottom = out.getbbox()
        self.assertLess(right - left, 101)
        self.assertGreater(bottom - top, 81)
        self.assertEqual(left + right, 201)
        self.assertEqual(top + bottom, 201)

    def test_invalid_settings_are_rejected(self):
        blur = load_script("reel_blur_v2")
        for fields in (
            {"scale_x": 0},
            {"motion_length": -1},
            {"softness": float("nan")},
            {"core_mix": 1.1},
        ):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                blur.Settings(**fields)

    def test_core_can_retain_fine_lines_inside_a_soft_motion_trail(self):
        blur = load_script("reel_blur_v2")
        pixels = np.zeros((101, 101, 4), dtype=np.uint8)
        pixels[35:66, 50] = (255, 200, 0, 255)
        source = Image.fromarray(pixels)
        result = blur.make_symbol(
            source, blur.Settings(motion_length=40, softness=4, core_mix=1)
        )
        self.assertTrue(np.array_equal(np.asarray(result), pixels))

    def test_cli_preserves_sources_and_refuses_existing_output(self):
        script = Path(__file__).resolve().parents[1] / "scripts/reel_blur_v2.py"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            source.mkdir()
            path = source / "sample.png"
            Image.new("RGBA", (101, 101), (255, 90, 0, 255)).save(path)
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            command = [
                sys.executable,
                "-I",
                str(script),
                "--source-dir",
                str(source),
                "--output-dir",
                str(root / "out"),
                "--preset",
                "coins",
            ]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((root / "out/manifest.json").read_text())
            self.assertEqual(report["outputs"][0]["settings"]["motion_length"], 30)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), before)
            again = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(again.returncode, 0)
            self.assertIn("existing", again.stderr.lower())

    def test_profile_applies_a_distinct_filter_per_file(self):
        blur = load_script("reel_blur_v2")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            source.mkdir()
            pixels = np.zeros((101, 101, 4), dtype=np.uint8)
            pixels[45:56, 45:56] = (255, 90, 0, 255)
            for name in ("coin.png", "symbol.png"):
                Image.fromarray(pixels).save(source / name)
            profile = {"files": {"coin.png": {"preset": "coins"}}}
            blur.build_set(source, root / "out", profile=profile)
            coin = Image.open(root / "out/coin.png")
            symbol = Image.open(root / "out/symbol.png")
            self.assertNotEqual(coin.tobytes(), symbol.tobytes())
            self.assertEqual(coin.getbbox()[2] - coin.getbbox()[0], 11)
            self.assertGreater(symbol.getbbox()[3] - symbol.getbbox()[1], 41)

    def test_profile_typo_is_rejected_before_creating_output(self):
        blur = load_script("reel_blur_v2")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            source.mkdir()
            Image.new("RGBA", (41, 41), "red").save(source / "coin.png")
            profile = {"files": {"coim.png": {"preset": "coins"}}}
            with self.assertRaises(ValueError):
                blur.build_set(source, root / "out", profile=profile)
            self.assertFalse((root / "out").exists())


if __name__ == "__main__":
    unittest.main()
