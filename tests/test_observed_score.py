import unittest

import polars as pl

from umnpmseac import AnalysisError, POINT_SCHEMA, PointPattern, score_observed_maxmin


def pattern(rows: list[tuple[str, float, float, str, int]]) -> PointPattern:
    return PointPattern(pl.DataFrame(rows, schema=POINT_SCHEMA, orient="row"))


class ObservedScoreTests(unittest.TestCase):
    def test_scores_only_the_two_observed_locations(self):
        points = pattern([
            ("sample-a", 0.0, 0.0, "A", 3),
            ("sample-a", 10.0, 0.0, "B", 2),
            ("sample-a", 0.0, 0.0, "A", 1),
        ])

        result = score_observed_maxmin(points, {"A": {"A"}, "B": {"B"}})

        self.assertEqual(result["x_um"].to_list(), [0.0, 10.0])
        self.assertEqual(result["maxmin_um"].to_list(), [10.0, 10.0])

    def test_scores_a_midpoint_only_when_it_was_observed(self):
        points = pattern([
            ("sample-a", 0.0, 0.0, "A", 1),
            ("sample-a", 5.0, 0.0, "OTHER", 1),
            ("sample-a", 10.0, 0.0, "B", 1),
        ])

        result = score_observed_maxmin(points, {"A": {"A"}, "B": {"B"}})

        self.assertEqual(result["x_um"].to_list(), [0.0, 5.0, 10.0])
        self.assertEqual(result["maxmin_um"].to_list(), [10.0, 5.0, 10.0])

    def test_keeps_samples_separate(self):
        points = pattern([
            ("sample-a", 0.0, 0.0, "A", 1),
            ("sample-a", 10.0, 0.0, "B", 1),
            ("sample-b", 0.0, 0.0, "A", 1),
            ("sample-b", 2.0, 0.0, "B", 1),
        ])

        result = score_observed_maxmin(points, {"A": {"A"}, "B": {"B"}})

        self.assertEqual(result.filter(pl.col("sample_id") == "sample-a")["maxmin_um"].to_list(), [10.0, 10.0])
        self.assertEqual(result.filter(pl.col("sample_id") == "sample-b")["maxmin_um"].to_list(), [2.0, 2.0])

    def test_rejects_missing_category_with_sample_name(self):
        points = pattern([("sample-a", 0.0, 0.0, "A", 1)])

        with self.assertRaisesRegex(AnalysisError, "sample 'sample-a'.*category 'B'"):
            score_observed_maxmin(points, {"A": {"A"}, "B": {"B"}})


if __name__ == "__main__":
    unittest.main()
