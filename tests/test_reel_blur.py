import importlib.util
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image


def load_script(name):
    path = Path(__file__).resolve().parents[1] / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReelBlurTests(unittest.TestCase):
    def test_vertical_filter_keeps_hidden_rgb_out_of_visible_edges(self):
        blur = load_script("reel_blur")
        data = np.zeros((41, 41, 4), dtype=np.uint8)
        data[..., 2] = 255
        data[15:26, 17:24] = (255, 100, 0, 255)
        result = np.asarray(blur.motion_blur(Image.fromarray(data), 4))
        visible = result[..., 3] > 0
        self.assertLessEqual(int(result[..., 2][visible].max()), 1)
        self.assertTrue(np.all(result[:, :17, 3] == 0))
        self.assertGreater(int(result[11, 20, 3]), 0)

    def test_three_copy_recipe_preserves_canvas_and_source(self):
        blur = load_script("reel_blur")
        data = np.zeros((400, 400, 4), dtype=np.uint8)
        data[100:300, 150:250] = (255, 160, 20, 255)
        source = Image.fromarray(data)
        result = blur.make_symbol(source)
        self.assertEqual(result.size, (400, 400))
        self.assertEqual(result.mode, "RGBA")
        self.assertTrue(np.array_equal(np.asarray(source), data))
        self.assertGreater(np.asarray(result)[80, 200, 3], 0)
        self.assertEqual(np.asarray(result)[0, 200, 3], 0)

    def test_safe_offsets_do_not_wrap_and_reject_invalid_radius(self):
        blur = load_script("reel_blur")
        source = Image.new("RGBA", (40, 40), (255, 200, 0, 255))
        self.assertEqual(blur.crop_safe_offset(source, -20), 0)
        self.assertEqual(blur.crop_safe_offset(source, 20), 0)
        shifted = np.asarray(blur.shift_y(source, 10))
        self.assertTrue(np.all(shifted[:10, :, 3] == 0))
        with self.assertRaises(ValueError):
            blur.make_symbol(source, radius=-1)

    def test_batch_maps_high_names_and_refuses_overwrite(self):
        blur = load_script("reel_blur")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            source.mkdir()
            Image.new("RGBA", (400, 400), (255, 160, 30, 255)).save(
                source / "high_symbol1.png"
            )
            report = blur.build_set(source, root / "out", abydos_names=True)
            self.assertTrue((root / "out/high1.png").exists())
            self.assertEqual(report["outputs"][0]["source"], "high_symbol1.png")
            with self.assertRaises(FileExistsError):
                blur.build_set(source, root / "out", abydos_names=True)

    def test_batch_rejects_mapping_collision_before_writing(self):
        blur = load_script("reel_blur")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            source.mkdir()
            for name in ("high_symbol1.png", "high1.png"):
                Image.new("RGBA", (40, 40), "gold").save(source / name)
            with self.assertRaises(ValueError):
                blur.build_set(source, root / "out", abydos_names=True)
            self.assertFalse((root / "out").exists())


if __name__ == "__main__":
    unittest.main()
