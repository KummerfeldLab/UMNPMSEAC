from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from umnpmseac import LoaderError, load_cosmx


def write_transcripts(path: Path) -> None:
    path.write_text(
        "fov,cell_ID,x_global_px,y_global_px,target\n"
        "10,1,100,200,IL6\n"
        "10,1,100,200,IL6\n"
        "11,2,300,400,CD3\n"
        "12,0,500,600,ACTB\n"
    )


class CosMxLoaderTests(unittest.TestCase):
    def test_controls_can_be_kept_or_removed(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "tx_file.csv"
            path.write_text(
                "fov,x_global_px,y_global_px,target\n"
                "10,1,2,IL6\n"
                "10,2,3,Negative7\n"
                "10,3,4,SystemControl115\n"
                "10,4,5,FalseCode1\n"
                "10,5,6,NegPrb2\n"
            )
            kept = load_cosmx(path, sample_id="sample-a", microns_per_pixel=0.18)
            removed = load_cosmx(
                path, sample_id="sample-a", microns_per_pixel=0.18,
                include_controls=False,
            )
            exact = load_cosmx(
                path, sample_id="sample-a", microns_per_pixel=0.18,
                include_controls=False, control_targets={"Negative7"},
            )

            self.assertEqual(kept.counts_per_sample(), {"sample-a": 5})
            self.assertEqual(removed.counts_per_sample(), {"sample-a": 1})
            self.assertEqual(removed.table["gene"].to_list(), ["IL6"])
            self.assertEqual(exact.counts_per_sample(), {"sample-a": 4})
            self.assertNotIn("Negative7", exact.table["gene"].to_list())

    def test_single_sample_slide_needs_no_fov_listing(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "tx_file.csv"
            write_transcripts(path)
            points = load_cosmx(path, sample_id="one-sample", microns_per_pixel=0.18)

            self.assertEqual(points.counts_per_sample(), {"one-sample": 4})

    def test_default_pixel_scale_can_be_overridden(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "tx_file.csv"
            write_transcripts(path)
            default = load_cosmx(path, sample_id="sample-a")
            override = load_cosmx(path, sample_id="sample-a", microns_per_pixel=0.18)

            self.assertEqual(default.table["x_um"][0], 12.028)
            self.assertEqual(override.table["x_um"][0], 18.0)

    def test_maps_fovs_converts_coordinates_and_preserves_molecules(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "tx_file.csv"
            write_transcripts(path)
            points = load_cosmx(
                path,
                fov_to_sample={10: "sample-a", 11: "sample-b", 12: None},
                microns_per_pixel=0.18,
            )

            self.assertEqual(points.sample_ids, ("sample-a", "sample-b"))
            self.assertEqual(points.counts_per_sample(), {"sample-a": 2, "sample-b": 1})
            self.assertEqual(points.for_sample("sample-a")["gene"].to_list(), ["IL6", "IL6"])
            self.assertEqual(points.for_sample("sample-a")["x_um"].to_list(), [18.0, 18.0])
            self.assertEqual(points.for_sample("sample-b")["y_um"].to_list(), [72.0])
            self.assertEqual(points.table["count"].to_list(), [1, 1, 1])

    def test_rejects_unmapped_fovs(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "tx_file.csv"
            write_transcripts(path)
            with self.assertRaisesRegex(LoaderError, "FOVs missing.*11, 12"):
                load_cosmx(path, fov_to_sample={10: "sample-a"}, microns_per_pixel=0.18)

    def test_requires_valid_scale_and_transcript_columns(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "tx_file.csv"
            write_transcripts(path)
            with self.assertRaisesRegex(LoaderError, "microns_per_pixel"):
                load_cosmx(path, fov_to_sample={10: "sample-a"}, microns_per_pixel=0)
            path.write_text("fov,target\n10,IL6\n")
            with self.assertRaisesRegex(LoaderError, "x_global_px, y_global_px"):
                load_cosmx(path, fov_to_sample={10: "sample-a"}, microns_per_pixel=0.18)


if __name__ == "__main__":
    unittest.main()
