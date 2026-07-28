import unittest
from urllib.parse import quote

from src.tools import parse_rental_listings, search_rentals_data


SAMPLE_HTML = """
<html><body>
  <div class="js__card">
    <a class="js__product-link-for-product-id"
       href="/cho-thue-nha-tro-phong-tro-cau-giay/phong-dep-pr123456"
       title="Phòng đẹp full nội thất Cầu Giấy">Xem tin</a>
    <span class="re__card-config-price">3,8 triệu/tháng</span>
    <span class="re__card-config-area">25 m²</span>
    <div class="re__card-location">Q. Cầu Giấy, Hà Nội</div>
    <div class="re__card-description">Có điều hòa, ban công và máy giặt.</div>
    <span class="re__card-published-info-published-at">Đăng hôm nay</span>
  </div>
  <div class="js__card">
    <a href="/cho-thue-can-ho-chung-cu-nam-tu-liem/can-ho-studio-pr789012"
       title="Căn hộ studio Nam Từ Liêm">Xem tin</a>
    <span class="re__card-config-price">6 triệu/tháng</span>
    <span class="re__card-config-area">32 m2</span>
    <div class="re__card-location">Q. Nam Từ Liêm, Hà Nội</div>
    <div class="re__card-description">Nội thất cơ bản.</div>
  </div>
</body></html>
"""


class FakeResponse:
    status_code = 200
    text = SAMPLE_HTML

    def raise_for_status(self):
        return None


class FakeSession:
    def __init__(self):
        self.headers = {}
        self.requested_urls = []

    def get(self, url, timeout):
        self.requested_urls.append(url)
        return FakeResponse()


class BlockedThenSearchSession:
    def __init__(self):
        self.headers = {}

    def get(self, url, timeout):
        if "duckduckgo.com" not in url:
            response = FakeResponse()
            response.status_code = 403
            return response
        target = quote(
            "https://batdongsan.com.vn/"
            "cho-thue-nha-tro-phong-tro-cau-giay/"
            "gia-tu-3-trieu-den-5-trieu"
        )
        response = FakeResponse()
        response.text = f"""
        <div class="result">
          <a class="result__a"
             href="//duckduckgo.com/l/?uddg={target}">
             Phòng trọ Cầu Giấy giá 3 - 5 triệu
          </a>
          <a class="result__snippet">
             Phòng 25 m², 3,8 triệu/tháng, có ban công. Đăng hôm nay
          </a>
        </div>
        """
        return response


class RentalSearchTests(unittest.TestCase):
    def test_parser_extracts_listing_fields(self):
        results = parse_rental_listings(SAMPLE_HTML)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].price_million_per_month, 3.8)
        self.assertEqual(results[0].area_m2, 25)
        self.assertIn("pr123456", results[0].url)

    def test_search_filters_location_price_and_keyword(self):
        payload = search_rentals_data(
            location="Cau Giay",
            keyword="ban công",
            max_price=4,
            session=FakeSession(),
        )
        self.assertEqual(payload["count"], 1)
        self.assertEqual(
            payload["results"][0]["title"], "Phòng đẹp full nội thất Cầu Giấy"
        )

    def test_invalid_price_range_is_rejected(self):
        with self.assertRaises(ValueError):
            search_rentals_data(
                min_price=8,
                max_price=4,
                session=FakeSession(),
            )

    def test_no_keyword_uses_district_page(self):
        session = FakeSession()
        payload = search_rentals_data(
            location="Cầu Giấy",
            max_price=5,
            min_area=20,
            session=session,
        )
        self.assertGreater(payload["count"], 0)
        self.assertIn(
            "cho-thue-nha-tro-phong-tro-cau-giay",
            session.requested_urls[0],
        )

    def test_cloudflare_page_is_detected(self):
        with self.assertRaisesRegex(Exception, "Cloudflare"):
            parse_rental_listings("<title>Just a moment...</title>")

    def test_search_index_fallback_after_403(self):
        payload = search_rentals_data(
            location="Cầu Giấy",
            max_price=5,
            session=BlockedThenSearchSession(),
        )
        self.assertEqual(payload["count"], 1)
        self.assertEqual(
            payload["results"][0]["retrieval_method"],
            "search_index_snippet",
        )
        self.assertTrue(payload["results"][0]["url"].startswith(
            "https://batdongsan.com.vn/"
        ))


if __name__ == "__main__":
    unittest.main()
