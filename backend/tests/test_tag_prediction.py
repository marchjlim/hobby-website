import unittest

from routers.ai import (
    ListingDetailsSuggestion,
    SuggestedTag,
    build_prompt,
    keep_allowed_suggestions,
    parse_gemini_response,
    parse_gemini_tag_suggestions,
)


class KeepAllowedSuggestionsTest(unittest.TestCase):
    def test_filters_normalizes_deduplicates_and_sorts(self):
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

    def test_builds_prompt_with_allowed_tags(self):
        prompt = build_prompt(["RG", "Clear Color"])

        self.assertIn('["RG", "Clear Color"]', prompt)

    def test_builds_listing_details_prompt(self):
        prompt = build_prompt(["RG"], include_name=True)

        self.assertIn("suggest a listing name", prompt)
        self.assertIn('["RG"]', prompt)

    def test_parses_gemini_response(self):
        result = parse_gemini_tag_suggestions({
            "candidates": [{
                "content": {
                    "parts": [
                        {"thought": True, "text": "internal reasoning"},
                        {"text": '{"suggestions":[{"tag":"RG","confidence":0.9}]}'},
                    ]
                }
            }]
        })

        self.assertEqual(result.suggestions[0].tag, "RG")

    def test_parses_listing_details_response(self):
        result = parse_gemini_response(
            {
                "candidates": [{
                    "content": {
                        "parts": [{
                            "text": (
                                '{"name":"RG 1/144 Nu Gundam",'
                                '"suggestions":[{"tag":"RG","confidence":0.9}]}'
                            ),
                        }]
                    }
                }]
            },
            ListingDetailsSuggestion,
        )

        self.assertEqual(result.name, "RG 1/144 Nu Gundam")


if __name__ == "__main__":
    unittest.main()
