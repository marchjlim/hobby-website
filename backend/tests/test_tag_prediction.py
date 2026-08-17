import unittest

from routers.ai import (
    ListingDetailsSuggestion,
    SuggestedTag,
    build_prompt,
    keep_allowed_suggestions,
    parse_gemini_response,
)


class ListingSuggestionTest(unittest.TestCase):
    def test_filters_normalizes_deduplicates_and_sorts_tags(self):
        result = keep_allowed_suggestions(
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

    def test_builds_holistic_prompt(self):
        prompt = build_prompt(
            ["RG"],
            [{"name": "RG Nu Gundam", "price": 55, "carousell_price": 60}],
        )

        self.assertIn("sales description", prompt)
        self.assertIn("prices in SGD", prompt)
        self.assertIn('"name": "RG Nu Gundam"', prompt)
        self.assertIn('["RG"]', prompt)

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
                                    '"suggested_price":55,'
                                    '"suggested_carousell_price":60,'
                                    '"pricing_rationale":"Based on a comparable RG listing.",'
                                    '"suggestions":[{"tag":"RG","confidence":0.9}]}'
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
        self.assertEqual(result.suggested_price, 55)
        self.assertEqual(result.suggested_carousell_price, 60)


if __name__ == "__main__":
    unittest.main()
