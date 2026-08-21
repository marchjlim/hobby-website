import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import httpx

from services.gemini import parse_gemini_response, request_gemini
from services.listing_generation import (
    ListingDetailsSuggestion,
    PricingAnalysis,
    SuggestedTag,
    apply_pricing_analysis,
    best_product_match,
    build_prompt,
    build_pricing_prompt,
    calculate_pricing,
    get_price_comparables,
    keep_allowed_tag_suggestions,
    rank_price_comparables,
)


class ListingSuggestionTest(unittest.TestCase):
    def test_retries_gemini_503(self):
        request = httpx.Request("POST", "https://example.test")
        overloaded = httpx.Response(503, request=request, text="overloaded")
        success = httpx.Response(
            200,
            request=request,
            json={"candidates": [{"content": {"parts": [{"text": (
                '{"name":"RG 1/144 Nu Gundam",'
                '"description":"A Real Grade model kit.",'
                '"tag_suggestions":[]}'
            )}]}}]},
        )

        with (
            patch.dict(os.environ, {"GEMINI_API_KEY": "test"}),
            patch("services.gemini.httpx.post", side_effect=[overloaded, success]) as post,
            patch("services.gemini.time.sleep") as sleep,
        ):
            result = request_gemini("prompt", ListingDetailsSuggestion, attempts=5)

        self.assertEqual(result.name, "RG 1/144 Nu Gundam")
        self.assertEqual(post.call_count, 2)
        sleep.assert_called_once_with(0.5)

    def test_retries_gemini_connection_failure(self):
        request = httpx.Request("POST", "https://example.test")
        success = httpx.Response(
            200,
            request=request,
            json={"candidates": [{"content": {"parts": [{"text": (
                '{"name":"MG 1/100 Zaku II",'
                '"description":"A Master Grade model kit.",'
                '"tag_suggestions":[]}'
            )}]}}]},
        )

        with (
            patch.dict(os.environ, {"GEMINI_API_KEY": "test"}),
            patch("services.gemini.httpx.post", side_effect=[
                httpx.ConnectError("offline", request=request), success
            ]) as post,
            patch("services.gemini.time.sleep") as sleep,
        ):
            result = request_gemini("prompt", ListingDetailsSuggestion, attempts=5)

        self.assertEqual(result.name, "MG 1/100 Zaku II")
        self.assertEqual(post.call_count, 2)
        sleep.assert_called_once_with(0.5)

    def test_selects_closest_product_name(self):
        match = best_product_match("MG 1/100 Zaku II Ver 2.0", [
            {"id": 1, "canonical_name": "MG 1/100 GUNDAM MK-II"},
            {"id": 2, "canonical_name": "MG 1/100 MS-06J ZAKU II VER.2.0"},
        ])

        self.assertEqual(match["id"], 2)

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

        self.assertIn("only about the model itself", prompt)
        self.assertIn("Do not explain grades", prompt)
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

    def test_prioritizes_inactive_same_product_and_enriches_tag_matches(self):
        class Query:
            def __init__(self, data):
                self.data = data

            def __getattr__(self, _name):
                return lambda *_args, **_kwargs: self

            def execute(self):
                return SimpleNamespace(data=self.data)

        responses = iter([
            [{
                "id": 1,
                "product_id": 10,
                "name": "Previous Nu Gundam",
                "price": 50,
                "carousell_price": 55,
                "created_at": "2026-01-01",
                "is_active": False,
            }],
            [{"ListingId": 2, "TagName": "RG"}],
            [{
                "id": 2,
                "product_id": 20,
                "name": "Comparable RG",
                "price": 45,
                "carousell_price": 50,
                "created_at": "2026-02-01",
                "is_active": True,
            }],
            [{
                "id": 20,
                "canonical_name": "RG 1/144 Sazabi",
                "grade": "RG",
                "scale": "1/144",
            }],
        ])

        class Client:
            def table(self, _name):
                return Query(next(responses))

        target = {
            "id": 10,
            "canonical_name": "RG 1/144 Nu Gundam",
            "grade": "RG",
            "scale": "1/144",
        }
        comparables = get_price_comparables(Client(), ["RG"], target)

        self.assertEqual([item["id"] for item in comparables], [1, 2])
        self.assertEqual(comparables[0]["retrieval_tier"], "same_product")
        self.assertEqual(
            comparables[1]["product_metadata"]["canonical_name"],
            "RG 1/144 Sazabi",
        )
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

    def test_pricing_analyst_is_grounded_in_retrieved_evidence(self):
        pricing = calculate_pricing([
            {"id": 1, "name": "A", "price": 40, "carousell_price": 45,
             "matched_tags": ["RG"]},
            {"id": 2, "name": "B", "price": 60, "carousell_price": 65,
             "matched_tags": ["RG"]},
        ])

        prompt = build_pricing_prompt("RG Nu Gundam", ["RG"], pricing)
        result = apply_pricing_analysis(
            pricing,
            PricingAnalysis(
                suggested_price=55,
                suggested_carousell_price=100,
                rationale="Closest RG comparables support the website price.",
            ),
        )

        self.assertIn('"comparables"', prompt)
        self.assertEqual(result["suggested_price"], 55)
        self.assertEqual(result["suggested_carousell_price"], 55)
        self.assertIn("Closest RG", result["pricing_rationale"])

if __name__ == "__main__":
    unittest.main()
