import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json
import os
from datetime import datetime
from compare import SectionBySectionRuleComparator


class TestTemporalRuleComparisons(unittest.TestCase):
    """Test cases for different temporal comparison scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_metadata = [
            {
                "text": "Test chunk from 2022 final rule",
                "metadata": {
                    "program": "MPFS",
                    "year": 2022,
                    "rule_type": "Final",
                    "source_file": "mpfs-2022-final.pdf"
                },
                "section_header": "Payment Updates"
            },
            {
                "text": "Test chunk from 2023 final rule", 
                "metadata": {
                    "program": "MPFS",
                    "year": 2023,
                    "rule_type": "Final",
                    "source_file": "mpfs-2023-final.pdf"
                },
                "section_header": "Fee Schedule"
            },
            {
                "text": "Test chunk from 2024 proposed rule",
                "metadata": {
                    "program": "MPFS",
                    "year": 2024,
                    "rule_type": "Proposed",
                    "source_file": "mpfs-2024-proposed.pdf"
                },
                "section_header": "Quality Measures"
            },
            {
                "text": "Test chunk from 2024 final rule",
                "metadata": {
                    "program": "MPFS", 
                    "year": 2024,
                    "rule_type": "Final",
                    "source_file": "mpfs-2024-final.pdf"
                },
                "section_header": "Payment Rates"
            },
            {
                "text": "Test chunk from 2025 final rule",
                "metadata": {
                    "program": "MPFS",
                    "year": 2025,
                    "rule_type": "Final", 
                    "source_file": "mpfs-2025-final.pdf"
                },
                "section_header": "Updates"
            }
        ]
        
        # Create temporary files
        self.temp_index = tempfile.NamedTemporaryFile(delete=False)
        self.temp_metadata = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        json.dump(self.mock_metadata, self.temp_metadata)
        self.temp_metadata.close()
        
        # Mock the current year to 2024 for consistent testing
        self.current_year = 2024
        
        with patch('faiss.read_index'), \
             patch('compare.datetime') as mock_datetime:
            mock_datetime.now.return_value.year = self.current_year
            self.comparator = SectionBySectionRuleComparator(
                faiss_index_path=self.temp_index.name,
                metadata_path=self.temp_metadata.name,
                api_key="test-api-key"
            )

    def tearDown(self):
        """Clean up temporary files"""
        os.unlink(self.temp_index.name)
        os.unlink(self.temp_metadata.name)


class TestCase1_NoYearsMentioned(TestTemporalRuleComparisons):
    """Test Case 1: Comparison of rules when years are not mentioned in prompts"""
    
    def test_no_years_defaults_to_current_and_previous(self):
        """When no years mentioned, should default to current year final vs previous year final"""
        queries = [
            "Compare MPFS final rules for fee schedule updates",
            "Analyze changes in SNF payment methodology between final rules",
            "What are the differences in Hospice quality measures in final rules?",
            "Compare final rule changes for wage index"
        ]
        
        for query in queries:
            with self.subTest(query=query):
                with patch('compare.datetime') as mock_datetime:
                    mock_datetime.now.return_value.year = 2024
                    
                    rule1, rule2, topic = self.comparator.parse_comparison_query(query)
                    
                    # Should default to previous year (2023) vs current year (2024)
                    self.assertEqual(rule1["year"], 2023)
                    self.assertEqual(rule2["year"], 2024)
                    self.assertEqual(rule1["rule_type"], "Final")
                    self.assertEqual(rule2["rule_type"], "Final")

    def test_no_years_no_rule_type_mentioned(self):
        """When neither years nor rule types mentioned, should use final rules"""
        query = "Compare MPFS payment updates"
        
        with patch('compare.datetime') as mock_datetime:
            mock_datetime.now.return_value.year = 2024
            
            rule1, rule2, topic = self.comparator.parse_comparison_query(query)
            
            self.assertEqual(rule1["year"], 2023)  # Previous year
            self.assertEqual(rule2["year"], 2024)  # Current year
            self.assertEqual(rule1["rule_type"], "Final")
            self.assertEqual(rule2["rule_type"], "Final")
            self.assertIn("payment", topic.lower())

    def test_no_years_different_programs(self):
        """Test default year assignment for different programs"""
        test_programs = [
            ("Compare MPFS updates", "MPFS"),
            ("Analyze SNF changes", "SNF"), 
            ("Review Hospice modifications", "Hospice")
        ]
        
        for query, expected_program in test_programs:
            with self.subTest(query=query, program=expected_program):
                with patch('compare.datetime') as mock_datetime:
                    mock_datetime.now.return_value.year = 2024
                    
                    rule1, rule2, topic = self.comparator.parse_comparison_query(query)
                    
                    self.assertEqual(rule1["program"], expected_program)
                    self.assertEqual(rule2["program"], expected_program)
                    self.assertEqual(rule1["year"], 2023)
                    self.assertEqual(rule2["year"], 2024)

    @patch('compare.datetime')
    def test_no_years_edge_case_january(self, mock_datetime):
        """Test behavior when current date is early in the year"""
        # Simulate January 2024
        mock_datetime.now.return_value.year = 2024
        
        query = "Compare final rules for payment changes"
        rule1, rule2, topic = self.comparator.parse_comparison_query(query)
        
        # Should still compare 2023 vs 2024
        self.assertEqual(rule1["year"], 2023)
        self.assertEqual(rule2["year"], 2024)


class TestCase2_CurrentYearProposedVsFinal(TestTemporalRuleComparisons):
    """Test Case 2: Comparison between current year proposed rule and final rule"""
    
    def test_explicit_proposed_vs_final_current_year(self):
        """Test explicit proposed vs final comparison for current year"""
        queries = [
            "Compare 2024 MPFS proposed rule with final rule",
            "Analyze differences between SNF 2024 proposed and final rules",
            "What changed from Hospice proposed to final rule in 2024?",
            "Review MPFS 2024 proposed rule versus final rule for quality measures"
        ]
        
        for query in queries:
            with self.subTest(query=query):
                rule1, rule2, topic = self.comparator.parse_comparison_query(query)
                
                # Should identify same year, different rule types
                self.assertEqual(rule1["year"], rule2["year"])  # Same year
                self.assertEqual(rule1["year"], 2024)  # Current year from query
                self.assertIn(rule1["rule_type"], ["Proposed", "Final"])
                self.assertIn(rule2["rule_type"], ["Proposed", "Final"])
                self.assertNotEqual(rule1["rule_type"], rule2["rule_type"])  # Different types

    def test_implicit_current_year_proposed_vs_final(self):
        """Test when current year is implied, not explicit"""
        queries = [
            "Compare MPFS proposed rule with final rule",
            "Differences between SNF proposed and final rules", 
            "Analyze proposed vs final rule changes for quality reporting"
        ]
        
        for query in queries:
            with self.subTest(query=query):
                with patch('compare.datetime') as mock_datetime:
                    mock_datetime.now.return_value.year = 2024
                    
                    rule1, rule2, topic = self.comparator.parse_comparison_query(query)
                    
                    # When both proposed and final mentioned without year, 
                    # should assume current year
                    self.assertEqual(rule1["year"], 2024)
                    self.assertEqual(rule2["year"], 2024)
                    self.assertIn("Proposed", [rule1["rule_type"], rule2["rule_type"]])
                    self.assertIn("Final", [rule1["rule_type"], rule2["rule_type"]])

    def test_proposed_to_final_evolution_analysis(self):
        """Test queries asking about evolution from proposed to final"""
        queries = [
            "How did the MPFS rule change from proposed to final?",
            "What modifications were made between SNF proposed and final rules?",  
            "Track changes from Hospice proposed rule to final implementation"
        ]
        
        for query in queries:
            with self.subTest(query=query):
                with patch('compare.datetime') as mock_datetime:
                    mock_datetime.now.return_value.year = 2024
                    
                    rule1, rule2, topic = self.comparator.parse_comparison_query(query)
                    
                    # Should detect the evolutionary comparison
                    rule_types = {rule1["rule_type"], rule2["rule_type"]}
                    self.assertEqual(rule_types, {"Proposed", "Final"})
                    self.assertEqual(rule1["year"], rule2["year"])

    def test_partial_rule_type_mention(self):
        """Test when only one rule type is explicitly mentioned"""
        test_cases = [
            ("Compare MPFS 2024 proposed rule with current final", "Proposed", "Final"),
            ("Analyze 2024 final rule against the proposed version", "Final", "Proposed"),
            ("Review SNF final rule changes from proposed", "Proposed", "Final")
        ]
        
        for query, type1, type2 in test_cases:
            with self.subTest(query=query):
                rule1, rule2, topic = self.comparator.parse_comparison_query(query)
                
                rule_types = {rule1["rule_type"], rule2["rule_type"]}
                expected_types = {type1, type2}
                self.assertEqual(rule_types, expected_types)


class TestCase3_PreviousYearFinalVsCurrentYearFinal(TestTemporalRuleComparisons):
    """Test Case 3: Comparison between previous year final and current year final rule"""
    
    def test_explicit_consecutive_years_final_rules(self):
        """Test explicit comparison of consecutive years' final rules"""
        queries = [
            "Compare 2023 MPFS final rule with 2024 final rule",
            "Analyze changes from SNF 2023 final to 2024 final rule",
            "What are differences between Hospice 2023 and 2024 final rules?",
            "Review payment updates from 2023 final rule to 2024 final rule"
        ]
        
        for query in queries:
            with self.subTest(query=query):
                rule1, rule2, topic = self.comparator.parse_comparison_query(query)
                
                # Should identify consecutive years
                years = [rule1["year"], rule2["year"]]
                years.sort()
                self.assertEqual(years, [2023, 2024])
                self.assertEqual(rule1["rule_type"], "Final")
                self.assertEqual(rule2["rule_type"], "Final")

    def test_year_over_year_comparison_implicit(self):
        """Test year-over-year comparisons without explicit year mention"""
        queries = [
            "Compare MPFS final rule year over year changes",
            "Analyze annual changes in SNF final rules",
            "Year-over-year final rule updates for Hospice",
            "Annual comparison of final rule modifications"
        ]
        
        for query in queries:
            with self.subTest(query=query):
                with patch('compare.datetime') as mock_datetime:
                    mock_datetime.now.return_value.year = 2024
                    
                    rule1, rule2, topic = self.comparator.parse_comparison_query(query)
                    
                    # Should default to previous vs current year
                    self.assertEqual(rule1["year"], 2023)
                    self.assertEqual(rule2["year"], 2024)
                    self.assertEqual(rule1["rule_type"], "Final")
                    self.assertEqual(rule2["rule_type"], "Final")

    def test_trend_analysis_queries(self):
        """Test queries focused on trends and evolution"""
        queries = [
            "How have MPFS payment rates evolved in final rules?",
            "Track SNF quality measure changes across final rules",
            "Analyze progression of Hospice requirements in final rules",
            "Evolution of wage index methodology in final rules"
        ]
        
        for query in queries:
            with self.subTest(query=query):
                with patch('compare.datetime') as mock_datetime:
                    mock_datetime.now.return_value.year = 2024
                    
                    rule1, rule2, topic = self.comparator.parse_comparison_query(query)
                    
                    # Evolution queries should compare consecutive final rules
                    self.assertEqual(rule1["rule_type"], "Final")
                    self.assertEqual(rule2["rule_type"], "Final")
                    self.assertEqual(abs(rule1["year"] - rule2["year"]), 1)

    def test_current_vs_previous_explicit(self):
        """Test explicit current vs previous year mentions"""
        queries = [
            "Compare current MPFS final rule with previous year",
            "Analyze this year's SNF final rule against last year's",
            "Current vs previous year Hospice final rule changes"
        ]
        
        for query in queries:
            with self.subTest(query=query):
                with patch('compare.datetime') as mock_datetime:
                    mock_datetime.now.return_value.year = 2024
                    
                    rule1, rule2, topic = self.comparator.parse_comparison_query(query)
                    
                    years = [rule1["year"], rule2["year"]]
                    self.assertIn(2023, years)  # Previous year
                    self.assertIn(2024, years)  # Current year


class TestCase4_AnyTwoYearsAnyRuleTypes(TestTemporalRuleComparisons):
    """Test Case 4: Comparison between any two years of any kind of rule types"""

    def test_multiple_years_mentioned(self):
        """Test queries with multiple years mentioned"""
        queries = [
            "Compare MPFS rules from 2020, 2022, and 2024",  # Should pick first and last
            "Analyze SNF changes across 2021, 2022, 2023 final rules",
            "Review Hospice evolution from 2019 through 2024"
        ]
        
        for query in queries:
            with self.subTest(query=query):
                rule1, rule2, topic = self.comparator.parse_comparison_query(query)
                
                # Should handle multiple years by selecting appropriate ones
                # Implementation should pick meaningful comparison pairs
                self.assertIsInstance(rule1["year"], int)
                self.assertIsInstance(rule2["year"], int)
                self.assertNotEqual(rule1["year"], rule2["year"])

    def test_historical_comparison_patterns(self):
        """Test various historical comparison patterns"""
        test_patterns = [
            ("How did MPFS change from 2018 final to 2023 proposed?", [2018, 2023]),
            ("Compare SNF 2017 proposed with 2021 final rule", [2017, 2021]),
            ("Analyze decade of changes: 2015 vs 2025 Hospice rules", [2015, 2025]),
            ("Pre-pandemic vs post-pandemic: 2019 final vs 2022 final MPFS", [2019, 2022])
        ]
        
        for query, expected_years in test_patterns:
            with self.subTest(query=query):
                rule1, rule2, topic = self.comparator.parse_comparison_query(query)
                
                actual_years = sorted([rule1["year"], rule2["year"]])
                expected_years.sort()
                self.assertEqual(actual_years, expected_years)

    def test_complex_temporal_relationships(self):
        """Test complex temporal relationship expressions"""
        queries = [
            "Compare the MPFS rule before COVID with the latest final rule",
            "Analyze SNF rules: pre-2020 vs current implementation", 
            "Early 2020s proposed vs mid-2020s final Hospice rules",
            "Compare inaugural vs most recent MPFS quality measures"
        ]
        
        for query in queries:
            with self.subTest(query=query):
                with patch('compare.datetime') as mock_datetime:
                    mock_datetime.now.return_value.year = 2024
                    
                    rule1, rule2, topic = self.comparator.parse_comparison_query(query)
                    
                    # Should extract meaningful years even from complex expressions
                    self.assertIsInstance(rule1["year"], int)
                    self.assertIsInstance(rule2["year"], int)
                    self.assertGreaterEqual(rule1["year"], 2015)  # Reasonable bounds
                    self.assertLessEqual(rule2["year"], 2025)

    def test_rule_type_precedence_with_multiple_years(self):
        """Test rule type assignment when multiple years and types mentioned"""
        test_cases = [
            ("2020 proposed and 2022 final MPFS rules", ["Proposed", "Final"]),
            ("Compare 2019 final with 2021 proposed SNF rules", ["Final", "Proposed"]),
            ("Both 2018 and 2023 final Hospice rule comparison", ["Final", "Final"])
        ]
        
        for query, expected_types in test_cases:
            with self.subTest(query=query):
                rule1, rule2, topic = self.comparator.parse_comparison_query(query)
                
                actual_types = [rule1["rule_type"], rule2["rule_type"]]
                # Should match expected types (order may vary)
                self.assertEqual(set(actual_types), set(expected_types))


class TestTemporalParsingEdgeCases(TestTemporalRuleComparisons):
    """Test edge cases in temporal parsing logic"""
    
    def test_ambiguous_temporal_references(self):
        """Test handling of ambiguous temporal references"""
        ambiguous_queries = [
            "Compare recent MPFS changes",
            "Analyze latest SNF updates vs older version", 
            "Current Hospice rules compared to historical approach",
            "Modern vs traditional MPFS methodology"
        ]
        
        for query in ambiguous_queries:
            with self.subTest(query=query):
                with patch('compare.datetime') as mock_datetime:
                    mock_datetime.now.return_value.year = 2024
                    
                    # Should not raise exceptions, should provide reasonable defaults
                    try:
                        rule1, rule2, topic = self.comparator.parse_comparison_query(query)
                        self.assertIsInstance(rule1["year"], int)
                        self.assertIsInstance(rule2["year"], int)
                        self.assertIsInstance(rule1["rule_type"], str)
                        self.assertIsInstance(rule2["rule_type"], str)
                    except Exception as e:
                        self.fail(f"Ambiguous query failed: {query} - {e}")

    def test_partial_temporal_information(self):
        """Test handling of partial temporal information"""
        partial_queries = [
            "Compare MPFS 2023 with final rule",  # Missing type for 2023, missing year for final
            "Analyze SNF proposed vs 2024",  # Missing year for proposed, missing type for 2024
            "Review 2022 changes against current Hospice"  # Mixed explicit/implicit temporal refs
        ]
        
        for query in partial_queries:
            with self.subTest(query=query):
                with patch('compare.datetime') as mock_datetime:
                    mock_datetime.now.return_value.year = 2024
                    
                    rule1, rule2, topic = self.comparator.parse_comparison_query(query)
                    
                    # Should fill in missing information with reasonable defaults
                    self.assertIn(rule1["rule_type"], ["Final", "Proposed"])
                    self.assertIn(rule2["rule_type"], ["Final", "Proposed"])
                    self.assertIsInstance(rule1["year"], int)
                    self.assertIsInstance(rule2["year"], int)

    @patch('compare.datetime')
    def test_future_year_handling(self, mock_datetime):
        """Test handling of future years in queries"""
        mock_datetime.now.return_value.year = 2024
        
        future_queries = [
            "Compare 2024 MPFS with 2026 proposed rule",
            "Analyze 2025 vs 2027 SNF changes"
        ]
        
        for query in future_queries:
            with self.subTest(query=query):
                rule1, rule2, topic = self.comparator.parse_comparison_query(query)
                
                # Should handle future years gracefully
                years = [rule1["year"], rule2["year"]]
                self.assertTrue(any(year > 2024 for year in years))

    def test_very_old_year_handling(self):
        """Test handling of very old years"""
        old_queries = [
            "Compare 2010 MPFS with current rules",
            "Analyze 2005 SNF vs 2024 final rule"
        ]
        
        for query in old_queries:
            with self.subTest(query=query):
                with patch('compare.datetime') as mock_datetime:
                    mock_datetime.now.return_value.year = 2024
                    
                    rule1, rule2, topic = self.comparator.parse_comparison_query(query)
                    
                    # Should handle old years
                    years = [rule1["year"], rule2["year"]]
                    self.assertTrue(any(year < 2015 for year in years))


if __name__ == '__main__':
    # Run with detailed output
    unittest.main(verbosity=2, failfast=False)