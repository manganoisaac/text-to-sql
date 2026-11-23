import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent import score_violations
from agent.types import SanityViolationType, Violation
from query import _average_scores


class QueryConfidenceTests(unittest.TestCase):
    def make_violation(self, category):
        return Violation(category=category, reason="test", severity=0.5)

    def test_no_violations_gives_full_sanity_score(self):
        self.assertEqual(score_violations([]), 1.0)

    def test_each_unique_violation_reduces_sanity_score(self):
        violation = self.make_violation(SanityViolationType.DATE_RANGE)
        self.assertEqual(score_violations([violation]), 0.75)

    def test_duplicate_categories_count_once(self):
        violation = self.make_violation(SanityViolationType.DATE_RANGE)
        self.assertEqual(score_violations([violation, violation]), 0.75)

    def test_all_violation_categories_give_zero_sanity_score(self):
        violations = [self.make_violation(category) for category in SanityViolationType]
        self.assertEqual(score_violations(violations), 0.0)

    def test_confidence_averages_any_number_of_scores(self):
        self.assertEqual(_average_scores([0.8, 1.0, 0.9]), 0.9)

    def test_confidence_requires_at_least_one_score(self):
        with self.assertRaisesRegex(ValueError, "At least one"):
            _average_scores([])

    def test_confidence_rejects_scores_outside_unit_interval(self):
        with self.assertRaisesRegex(ValueError, "between 0 and 1"):
            _average_scores([0.8, 1.1])


if __name__ == "__main__":
    unittest.main()
