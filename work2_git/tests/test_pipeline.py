import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "generate_weekly_report.py"
spec = importlib.util.spec_from_file_location("generate_weekly_report", MODULE_PATH)
pipeline = importlib.util.module_from_spec(spec)
sys.modules["generate_weekly_report"] = pipeline
spec.loader.exec_module(pipeline)


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads((ROOT / "tests" / "fixtures" / "sample_signals.json").read_text(encoding="utf-8"))

    def test_youtube_score_increases_with_velocity_and_comments(self):
        profile = {
            "product_key": "dog-paw-washer",
            "name": "Dog Paw Washer",
            "pet": "Dog",
            "category": "Cleaning & Hygiene",
            "problem": "Muddy paw cleaning problem",
            "suggested_price": "TBD",
            "landing_page_angle": "TBD",
            "creative_angles": [],
            "test_plan": [],
            "risks": [],
        }
        weak = pipeline.build_product(
            profile,
            [
                {
                    "video_id": "a",
                    "query": "dog paw washer",
                    "title": "weak",
                    "description": "",
                    "channel_id": "c1",
                    "channel_title": "creator",
                    "published_at": "2026-05-01T00:00:00Z",
                    "url": "https://www.youtube.com/watch?v=a",
                    "views": 100,
                    "likes": 2,
                    "comments": 0,
                }
            ],
            [],
        )
        strong = pipeline.build_product(
            profile,
            [
                {
                    "video_id": str(i),
                    "query": "dog paw washer",
                    "title": "strong",
                    "description": "",
                    "channel_id": f"c{i}",
                    "channel_title": "creator",
                    "published_at": "2026-05-18T00:00:00Z",
                    "url": f"https://www.youtube.com/watch?v={i}",
                    "views": 50000,
                    "likes": 2500,
                    "comments": 300,
                }
                for i in range(6)
            ],
            [{"text": "This helps with muddy mess problem", "likes": 3} for _ in range(6)],
        )
        self.assertGreater(strong["score"], weak["score"])
        self.assertGreater(strong["scores"]["creator_diversity"], weak["scores"]["creator_diversity"])

    def test_food_and_supplements_are_filtered(self):
        products, excluded = pipeline.build_products(self.fixture["products"])
        self.assertTrue(all("treat" not in product["name"].lower() for product in products))
        self.assertTrue(any("treat" in product["name"].lower() for product in excluded))

    def test_discover_clusters_extracts_product_phrases(self):
        videos = [
            {
                "video_id": "a",
                "query": "pet cleaning hacks",
                "title": "Best dog paw washer for muddy walks",
                "description": "clean dirty paws fast",
                "channel_id": "c1",
                "channel_title": "creator",
                "published_at": "2026-05-18T00:00:00Z",
                "url": "https://www.youtube.com/watch?v=a",
                "views": 10000,
                "likes": 500,
                "comments": 30,
            },
            {
                "video_id": "b",
                "query": "dog gadgets",
                "title": "Paw washer gadget after rainy dog walk",
                "description": "muddy dog product review",
                "channel_id": "c2",
                "channel_title": "creator",
                "published_at": "2026-05-18T00:00:00Z",
                "url": "https://www.youtube.com/watch?v=b",
                "views": 15000,
                "likes": 700,
                "comments": 45,
            },
        ]
        clusters = pipeline.discover_clusters(videos, 5)
        self.assertTrue(clusters)
        self.assertTrue(any("washer" in cluster["profile"]["name"].lower() for cluster in clusters))
        self.assertFalse(any(cluster["profile"]["name"].lower() == "washer" for cluster in clusters))

    def test_generic_terms_are_not_specific_candidates(self):
        self.assertFalse(pipeline.is_specific_phrase("mat"))
        self.assertFalse(pipeline.is_specific_phrase("toy"))
        self.assertFalse(pipeline.is_specific_phrase("cover"))
        self.assertTrue(pipeline.is_specific_phrase("cat litter mat"))
        self.assertTrue(pipeline.is_specific_phrase("dog car seat cover"))

    def test_missing_key_does_not_create_fake_candidates(self):
        result = pipeline.fetch_youtube({}, None)
        report = pipeline.make_report(result, "2026-W21")
        self.assertEqual(report["products"], [])
        self.assertIn("disabled_missing_credentials", report["source_status"]["youtube"]["status"])

    def test_report_outputs_are_written(self):
        result = pipeline.source_from_fixture(self.fixture)
        report = pipeline.make_report(result, "2099-W01")
        with tempfile.TemporaryDirectory() as temp_dir:
            original = pipeline.REPORTS_DIR
            pipeline.REPORTS_DIR = Path(temp_dir)
            try:
                out = pipeline.write_outputs(report)
                self.assertTrue((out / "report.md").exists())
                self.assertTrue((out / "report.html").exists())
                self.assertTrue((out / "products.csv").exists())
                self.assertTrue((out / "evidence.json").exists())
                self.assertTrue((Path(temp_dir) / "latest.js").exists())
            finally:
                pipeline.REPORTS_DIR = original


if __name__ == "__main__":
    unittest.main()
