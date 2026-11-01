"""Standalone public preview checks; source publication packets are not needed."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from http.server import ThreadingHTTPServer

try:
    import selection_core as core
except ImportError:
    import nsfc_panel as core
from public_view import keyword_frequencies, rao_stirling, reader_materials, reader_status


class PublicPreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.materials = core.materials()
        cls.status = core.status()

    def test_distinct_paper_frequency(self):
        papers = [{"methods": ["Survey", "survey"]}, {"methods": ["SURVEY", "Regression"]}]
        self.assertEqual(keyword_frequencies(papers, "methods"), [
            {"term": "Survey", "paper_count": 2},
            {"term": "Regression", "paper_count": 1},
        ])

    def test_profiles_can_be_served_without_source_packets(self):
        expected = reader_materials(self.materials)
        source = copy.deepcopy(self.materials)
        source["derived_profiles"] = expected["experts"]
        source["experts"] = [{"id": e["id"], "field_shares": e["field_shares"]}
                             for e in expected["experts"]]
        self.assertEqual(reader_materials(source), expected)
        self.assertEqual(reader_materials(expected), expected)
        for e in expected["experts"]:
            self.assertEqual(e["publication_count"], 5)
            self.assertEqual(set(e["knowledge_profile"]), {"summary_en"})
            self.assertNotIn("papers", e)
            for key in ["topic_keywords", "method_keywords"]:
                self.assertTrue(e[key])
                self.assertTrue(all(1 <= term["paper_count"] <= e["publication_count"]
                                    for term in e[key]))

    def test_shared_geometry_and_breadth(self):
        delta = self.materials["geometry"]["delta"]
        expected = [0, .466050646, .438688177632, .629270620564, .430000000008]
        for e, value in zip(reader_materials(self.materials)["experts"], expected):
            self.assertAlmostEqual(sum(e["field_shares"].values()), 1)
            self.assertAlmostEqual(e["disciplinary_breadth"]["value"], value, places=8)
        for p in self.materials["projects"]:
            self.assertAlmostEqual(rao_stirling(p["field_shares"], delta),
                                   p["knowledge_design"]["span_D"], places=8)

    def test_saved_outputs_and_provenance_survive_projection(self):
        public = reader_status(self.status)
        self.assertEqual(len(public["records"]), 55)
        self.assertEqual(sum(r["task"] == "rubric" for r in public["records"]), 50)
        self.assertEqual(sum(r["task"] == "ranking" for r in public["records"]), 5)
        for original, record in zip(self.status["records"], public["records"]):
            self.assertEqual(record["parsed"], original["parsed"])
            self.assertEqual(record["input_sha256"], original["input_sha256"])
            self.assertNotIn("messages", record)
            self.assertNotIn("attempt_records", record)

    def test_saved_portfolio_arithmetic(self):
        for budget in [1, 3, 9]:
            result = core.evaluate(budget=budget, include_joint=True)
            self.assertEqual(result["status"], "actual_computation")
            for rule in result["rules"]:
                self.assertEqual(len(rule["selected"]), budget)
                self.assertAlmostEqual(rule["value"], sum(result["values"][p]
                                                         for p in rule["selected"]))
            if budget == 3:
                values = {rule["rule"]: rule["value"] for rule in result["rules"]}
                self.assertAlmostEqual(values["Mean score"], 2.525)
                self.assertAlmostEqual(values["Borda ranking"], 2.6625)
                for method in ["FV", "Greedy", "GreedyLocal", "ASTAR"]:
                    self.assertAlmostEqual(values[f"Joint MB · {method}"], 2.6625)
                self.assertAlmostEqual(values["Ranking (from scores)"], 2.5375)

    def test_official_fits_and_normalized_losses(self):
        artifact = core.read("rankrate_alignment.json")
        self.assertEqual(artifact["new_ai_calls"], 0)
        self.assertEqual(artifact["M"], 12)
        for budget in range(1, 10):
            result = core.evaluate(budget=budget, include_joint=True)
            for row in result["rules"]:
                self.assertAlmostEqual(row["loss_per_project"], row["loss"] / budget)
                saved = next((x for x in artifact["comparisons"]
                              if x["budget"] == budget and x["rule"] == row["rule"]), None)
                if saved:
                    self.assertEqual(row["selected"], saved["selected"])
                    self.assertAlmostEqual(row["value"], saved["value"])
            self.assertEqual(result["statistical_diagnostics"]["version"], "1.2.1")

    def test_frozen_fit_rejects_changed_evaluations(self):
        changed = copy.deepcopy(self.status)
        row = next(r for r in changed["records"] if r["task"] == "rubric")
        row["parsed"]["scores"][0]["score"] = 1
        with self.assertRaisesRegex(ValueError, "refitting is required"):
            core.evaluate(include_joint=True, provided=changed)

    def test_midpoint_voting_excludes_exactly_half_scale(self):
        result = core.evaluate()
        expected = {"P01": 5, "P02": 0, "P03": 3, "P04": 1, "P05": 5,
                    "P06": 0, "P07": 4, "P08": 0, "P09": 3, "P10": 0}
        self.assertEqual(result["vote_counts"], expected)
        boundary_reviews = 0
        for reviewer, scores in result["matrix"].items():
            for project, total in scores.items():
                reverse = result["reverse_scores"][reviewer][project]
                self.assertAlmostEqual(total, 100 * (1 - reverse / 12))
                if reverse == 6:
                    boundary_reviews += 1
                    self.assertEqual(total, 50)
                    self.assertFalse(reverse < 6)
        self.assertEqual(boundary_reviews, 18)
        selected = next(r for r in result["rules"]
                        if r["rule"] == "Voting (midpoint threshold)")
        self.assertEqual(selected["selected"], ["P01", "P05", "P07"])
        self.assertAlmostEqual(selected["value"], 2.525)
        self.assertAlmostEqual(selected["loss"], .1375)

    def test_supplementary_threshold_keeps_main_vote_fixed(self):
        low = core.evaluate(threshold=50)
        high = core.evaluate(threshold=70)
        self.assertEqual(low["vote_counts"], high["vote_counts"])
        self.assertEqual(low["categorical_vote_counts"], high["categorical_vote_counts"])
        self.assertNotEqual(low["utilities"]["Score-threshold vote (supplementary)"],
                            high["utilities"]["Score-threshold vote (supplementary)"])


class PublicPreviewRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        server_path = root / "cloud_server.py"
        if not server_path.exists():
            server_path = root / "deploy/cloud_server.py"
        spec = importlib.util.spec_from_file_location("public_preview_server_test", server_path)
        cloud = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"selection_core": core}):
            spec.loader.exec_module(cloud)
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), cloud.Handler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=3)

    def test_read_only_routes_and_output_projection(self):
        base = f"http://127.0.0.1:{self.httpd.server_port}"
        for route, expected in [
            ("/api/panel/materials", reader_materials(core.materials())),
            ("/api/panel/results", reader_status(core.status())),
        ]:
            with urlopen(base + route, timeout=5) as response:
                self.assertEqual(json.load(response), expected)
        with self.assertRaises(HTTPError) as rejected:
            urlopen(Request(base + "/api/panel/run", data=b"{}", method="POST"), timeout=5)
        self.assertEqual(rejected.exception.code, 405)


if __name__ == "__main__":
    unittest.main()
