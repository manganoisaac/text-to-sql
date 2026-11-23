import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent import score_violations
from agent.sql_agent import _sql_matches, call_llm
from agent.types import QueryComplexity, SanityViolationType, SQLResult, Violation
from query import _average_scores
from unittest.mock import patch


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

    def test_sql_match_ignores_formatting_and_keyword_case(self):
        self.assertTrue(
            _sql_matches(
                "select * from orders where total > 10;",
                "SELECT *\nFROM orders\nWHERE total > 10",
            )
        )

    def test_sql_match_rejects_different_queries(self):
        self.assertFalse(
            _sql_matches(
                "SELECT * FROM orders WHERE total > 10",
                "SELECT * FROM orders WHERE total > 100",
            )
        )

    @patch("agent.sql_agent._generate_sql")
    @patch("agent.sql_agent.get_llm")
    def test_complex_queries_use_two_strategies_and_record_agreement(
        self, get_llm, generate_sql
    ):
        classifier = get_llm.return_value.with_structured_output.return_value
        classifier.invoke.return_value = QueryComplexity(
            is_complex=True, reason="Multiple joins and aggregations"
        )
        generate_sql.side_effect = [
            SQLResult(
                sql_query="SELECT COUNT(*) FROM orders",
                explanation="Count orders",
                confidence=0.8,
                tables_and_columns=[],
            ),
            SQLResult(
                sql_query="select count(*) from orders;",
                explanation="Count orders",
                confidence=0.8,
                tables_and_columns=[],
            ),
        ]

        result = call_llm({"messages": [], "user_query": "Count orders"})

        self.assertEqual(generate_sql.call_count, 2)
        self.assertEqual(
            [call.args[1] for call in generate_sql.call_args_list],
            [
                "Generate the clearest direct SQL solution. Prefer a straightforward SELECT "
                "with explicit joins and avoid CTEs unless they materially improve clarity.",
                "Independently solve the question by first decomposing it into logical steps. "
                "Prefer named CTEs for those steps, and verify joins, filters, and aggregation "
                "against the requested result before returning SQL.",
            ],
        )
        self.assertEqual(result["sql_agreement"], 1.0)

    @patch("agent.sql_agent._generate_sql")
    @patch("agent.sql_agent.get_llm")
    def test_simple_queries_use_one_generation_and_no_agreement_score(
        self, get_llm, generate_sql
    ):
        get_llm.return_value.with_structured_output.return_value.invoke.return_value = (
            QueryComplexity(is_complex=False, reason="Simple lookup")
        )
        generate_sql.return_value = SQLResult(
            sql_query="SELECT * FROM orders",
            explanation="List orders",
            confidence=0.8,
            tables_and_columns=[],
        )

        result = call_llm({"messages": [], "user_query": "List orders"})

        generate_sql.assert_called_once_with([])
        self.assertIsNone(result["sql_agreement"])


if __name__ == "__main__":
    unittest.main()
