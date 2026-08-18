import unittest

from routers.ai import (
    ListingDetailsSuggestion,
    SuggestedTag,
    build_prompt,
    calculate_pricing,
    keep_allowed_tag_suggestions,
    parse_gemini_response,
    rank_price_comparables,
)


class ListingSuggestionTest(unittest.TestCase):
    def test_filters_normalizes_deduplicates_and_sorts_tags(self):
        result = keep_allowed_tag_suggestions(
            [
                SuggestedTag(tag="rg", confidence=0.4),
                SuggestedTag(tag="invented", confidence=1),
                SuggestedTag(tag="RG", confidence=0.8),
                SuggestedTag(tag="Clear Color", confidence=0.9),
            ],
            ["RG", "Clear Color"],
        )

        self.assertEqual([item.tag for item in result], ["Clear Color", "RG"])
        self.assertEqual(result[1].confidence, 0.8)

    def test_builds_extraction_prompt(self):
        prompt = build_prompt(["RG"])

        self.assertIn("sales description", prompt)
        self.assertIn('["RG"]', prompt)
        self.assertNotIn("prices in SGD", prompt)

    def test_parses_listing_details_response(self):
        result = parse_gemini_response(
            {
                "candidates": [{
                    "content": {
                        "parts": [
                            {"thought": True, "text": "internal reasoning"},
                            {
                                "text": (
                                    '{"name":"RG 1/144 Nu Gundam",'
                                    '"description":"A Real Grade model kit.",'
                                    '"tag_suggestions":[{"tag":"RG","confidence":0.9}]}'
                                ),
                            },
                        ]
                    }
                }]
            },
            ListingDetailsSuggestion,
        )

        self.assertEqual(result.name, "RG 1/144 Nu Gundam")
        self.assertEqual(result.description, "A Real Grade model kit.")
        self.assertEqual(result.tag_suggestions[0].tag, "RG")


    def test_ranks_comparables_by_weighted_tag_overlap(self):
        listings = [
            {
                "id": 1,
                "name": "Strong match",
                "price": 50,
                "carousell_price": 55,
                "created_at": "2026-01-01T00:00:00Z",
            },
            {
                "id": 2,
                "name": "Weak match",
                "price": 40,
                "carousell_price": 45,
                "created_at": "2026-02-01T00:00:00Z",
            },
        ]
        relationships = [
            {"ListingId": 1, "TagName": "RG"},
            {"ListingId": 1, "TagName": "1/144"},
            {"ListingId": 2, "TagName": "Clear Color"},
        ]

        ranked = rank_price_comparables(
            listings,
            relationships,
            ["RG", "1/144", "Clear Color"],
        )

        self.assertEqual([item["id"] for item in ranked], [1, 2])
        self.assertEqual(ranked[0]["match_score"], 6)
        self.assertEqual(ranked[1]["match_score"], 2)

    def test_calculates_median_prices(self):
        comparables = [
            {
                "id": 1,
                "price": 40,
                "carousell_price": 50,
                "matched_tags": ["RG"],
            },
            {
                "id": 2,
                "price": 60,
                "carousell_price": 70,
                "matched_tags": ["RG"],
            },
            {
                "id": 3,
                "price": 100,
                "carousell_price": None,
                "matched_tags": ["1/144"],
            },
        ]

        pricing = calculate_pricing(comparables)

        self.assertEqual(pricing["suggested_price"], 60)
        self.assertEqual(pricing["suggested_carousell_price"], 60)
        self.assertEqual(pricing["comparable_count"], 3)

    def test_requires_two_comparable_prices(self):
        pricing = calculate_pricing([
            {
                "id": 1,
                "price": 40,
                "carousell_price": None,
                "matched_tags": ["RG"],
            }
        ])

        self.assertIsNone(pricing["suggested_price"])
        self.assertIsNone(pricing["suggested_carousell_price"])


    def test_uses_sgd_msrp_as_a_fallback(self):
        pricing = calculate_pricing(
            [],
            {
                "msrp": 55,
                "msrp_currency": "SGD",
                "last_reproduction_date": "2025-01-01",
            },
        )

        self.assertEqual(pricing["suggested_price"], 55)
        self.assertIsNone(pricing["suggested_carousell_price"])
        self.assertIn("SGD MSRP", pricing["pricing_rationale"])


if __name__ == "__main__":
    unittest.main()
