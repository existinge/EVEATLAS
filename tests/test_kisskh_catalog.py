"""Offline tests for the KissKH catalog metadata adapter; no live site calls."""
import unittest
from urllib.parse import parse_qs, urlsplit

from tools.kisskh_catalog import (
    CatalogError, KissKHCatalog, _extract_rows, normalize, screen
)


class CatalogTests(unittest.TestCase):
    def make_client(self, response):
        seen = []
        def fake(url):
            seen.append(url)
            return response
        return KissKHCatalog(transport=fake), seen

    def test_list_query_parameters(self):
        client, seen = self.make_client({"data": []})
        response, source = client.list_page(page=2, page_size=20)
        self.assertEqual(response, {"data": []})
        self.assertEqual(seen, [source])
        parsed = urlsplit(source)
        self.assertEqual(parsed.path, "/api/DramaList/List")
        self.assertEqual(parse_qs(parsed.query)["page"], ["2"])
        self.assertEqual(parse_qs(parsed.query)["pageSize"], ["20"])
        self.assertEqual(parse_qs(parsed.query)["type"], ["0"])

    def test_search_url_encodes_text(self):
        client, seen = self.make_client([])
        _, url = client.search(" love & BL ")
        self.assertEqual(seen[0], url)
        self.assertEqual(urlsplit(url).path, "/api/DramaList/Search")
        self.assertEqual(parse_qs(urlsplit(url).query), {"q":["love & BL"],"type":["0"]})

    def test_detail_endpoint(self):
        client, seen = self.make_client({"data":{"id":4608,"title":"Sample"}})
        _, url = client.drama(4608)
        self.assertEqual(urlsplit(url).path, "/api/DramaList/Drama/4608")
        self.assertEqual(parse_qs(urlsplit(url).query), {"isq":["false"]})
        self.assertEqual(seen, [url])

    def test_rejects_bad_base_and_ids(self):
        for url in ("http://kisskh.is", "https://kisskh.is.evil.test",
                    "https://user@kisskh.is", "https://kisskh.is/bypass",
                    "https://kisskh.is:444", "https://localhost"):
            with self.subTest(url=url), self.assertRaises(CatalogError):
                KissKHCatalog(base_url=url)
        client, _ = self.make_client([])
        for bad in ("../../thing", -1, 0, "42/stream", True):
            with self.subTest(id=bad), self.assertRaises(CatalogError):
                client.drama(bad)

    def test_rejects_broad_queries_and_big_pages(self):
        client, _ = self.make_client([])
        with self.assertRaises(CatalogError):
            client.search("")
        with self.assertRaises(CatalogError):
            client.list_page(page_size=500)

    def test_supported_list_and_detail_envelopes(self):
        self.assertEqual(_extract_rows({"data":[{"id":1}]}), [{"id":1}])
        self.assertEqual(_extract_rows({"data":{"items":[{"id":2}]}}), [{"id":2}])
        self.assertEqual(_extract_rows({"data":{"id":3,"title":"x"}}, detail=True),
                         [{"id":3,"title":"x"}])
        with self.assertRaises(CatalogError):
            _extract_rows({"surprise":"invalid"})

    def test_unicode_aliases_remain_distinct(self):
        item = normalize({"id":123,"title":"Love Name",
                          "originalTitle":"恋の名前",
                          "alternativeTitles":["Another Name", "Love Name"]},
                          "https://kisskh.is/api/DramaList/Search?q=love&type=0")
        self.assertEqual(item["aliases"], ["恋の名前", "Another Name"])
        self.assertIsNone(item["central_mm_romance"])
        self.assertIsNone(item["released"])
        self.assertEqual(item["sources"], [])

    def test_known_title_or_alias_blocks_discovery(self):
        response = {"data":[{"id":10,"title":"New English", "originalTitle":"旧名"}]}
        result = screen(response, "https://kisskh.is/api/DramaList/Search?q=x&type=0",
                        known_titles=[{"title":"Known Title","aliases":["旧名"],
                                       "status":"Already Seen"}])
        entry = result["screening"]["results"][0]
        self.assertEqual(entry["disposition"], "blocked")
        self.assertEqual(result["screening"]["discovered"], 0)

    def test_unknown_is_research_lead_not_verified_bl(self):
        response = {"data":[{"id":4608,"title":"A Business Proposal"}]}
        result = screen(response, "https://kisskh.is/api/DramaList/Drama/4608?isq=false")
        self.assertEqual(result["screening"]["verified"], 0)
        self.assertEqual(result["screening"]["research_leads"], 1)
        self.assertFalse(result["live_playback_verified"])
        gaps = result["screening"]["results"][0]["research_gaps"]
        self.assertIn("central_romance_unverified", gaps)
        self.assertIn("missing_evidence", gaps)

    def test_invalid_item_rejected_instead_of_skipped(self):
        with self.assertRaises(CatalogError):
            normalize({"id": 12}, "https://kisskh.is/x")
        with self.assertRaises(CatalogError):
            normalize({"title": "Untitled"}, "https://kisskh.is/x")


if __name__ == "__main__":
    unittest.main()
