import unittest

from routers.ai import (
    SuggestedTag,
    build_prompt,
    keep_allowed_suggestions,
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


if __name__ == "__main__":
    unittest.main()
