import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np
from PIL import Image


class CompareBlurTests(unittest.TestCase):
    def test_cli_builds_both_variants_and_keeps_choices_pending(self):
        script = Path(__file__).resolve().parents[1] / "scripts/compare_reel_blur.py"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            source.mkdir()
            pixels = np.zeros((200, 200, 4), dtype=np.uint8)
            pixels[65:135, 70:130] = (255, 150, 20, 255)
            path = source / "symbol.png"
            Image.fromarray(pixels).save(path)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            command = [
                sys.executable,
                "-I",
                str(script),
                "--source-dir",
                str(source),
                "--output-dir",
                str(root / "out"),
            ]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            v1 = Image.open(root / "out/v1/symbol.png")
            v2 = Image.open(root / "out/v2/symbol.png")
            self.assertEqual(v1.size, (200, 200))
            self.assertEqual(v2.size, v1.size)
            self.assertNotEqual(v1.tobytes(), v2.tobytes())
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)
            self.assertTrue((root / "out/contact-01.png").exists())
            self.assertTrue((root / "out/contact-checker-01.png").exists())
            selection = json.loads((root / "out/selection.json").read_text())
            self.assertEqual(selection, {"symbol.png": None})
            second = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("existing", second.stderr.lower())

    def test_contact_pages_cover_the_whole_catalog(self):
        script = Path(__file__).resolve().parents[1] / "scripts/compare_reel_blur.py"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            source.mkdir()
            for i in range(7):
                Image.new("RGBA", (80, 80), (255, 100, 0, 180)).save(
                    source / f"{i}.png"
                )
            result = subprocess.run(
                [
                    sys.executable,
                    "-I",
                    str(script),
                    "--source-dir",
                    str(source),
                    "--output-dir",
                    str(root / "out"),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((root / "out/comparison.json").read_text())
            self.assertEqual(len(report["symbols"]), 7)
            self.assertEqual(len(report["contact_sheets"]), 2)
            self.assertTrue((root / "out/contact-02.png").exists())


if __name__ == "__main__":
    unittest.main()
