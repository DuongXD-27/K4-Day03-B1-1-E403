"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi.
"""

import json
import re
import time
import unicodedata
from dataclasses import asdict, dataclass
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BATDONGSAN_BASE_URL = "https://batdongsan.com.vn"
RENTAL_URLS = {
    "phong_tro": f"{BATDONGSAN_BASE_URL}/cho-thue-nha-tro-phong-tro-ha-noi",
    "can_ho": f"{BATDONGSAN_BASE_URL}/cho-thue-can-ho-chung-cu-ha-noi",
}


class RentalSearchError(RuntimeError):
    """Lỗi có thể hiển thị trực tiếp cho người dùng khi tra cứu tin thuê."""


@dataclass
class RentalListing:
    title: str
    price: str
    price_million_per_month: Optional[float]
    area_m2: Optional[float]
    location: str
    description: str
    posted_at: str
    url: str
    verified: bool
    property_type: str


def _plain_text(value: str) -> str:
    """Chuẩn hóa chuỗi để tìm kiếm tiếng Việt không phân biệt dấu."""
    value = unicodedata.normalize("NFD", value or "")
    return "".join(ch for ch in value if unicodedata.category(ch) != "Mn").lower()


def _number(value: str) -> float:
    return float(value.replace(".", "").replace(",", "."))


def _parse_price(text: str) -> tuple[str, Optional[float]]:
    matches = re.search(
        r"(\d+(?:[.,]\d+)?)\s*(triệu|tr|nghìn|ngàn)\s*/?\s*tháng",
        text,
        flags=re.IGNORECASE,
    )
    if not matches:
        if "thỏa thuận" in _plain_text(text):
            return "Thỏa thuận", None
        return "Không rõ", None

    amount = _number(matches.group(1))
    unit = _plain_text(matches.group(2))
    if unit in {"nghin", "ngan"}:
        amount /= 1000
    return matches.group(0).strip(), round(amount, 3)


def _parse_area(text: str) -> Optional[float]:
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*m(?:²|2)\b", text, flags=re.IGNORECASE)
    return _number(match.group(1)) if match else None


def _first_text(node, selectors: tuple[str, ...]) -> str:
    for selector in selectors:
        found = node.select_one(selector)
        if found:
            value = found.get_text(" ", strip=True)
            if value:
                return value
    return ""


def _listing_container(link):
    """Tìm card chứa link tin, kể cả khi website đổi một phần tên class."""
    for parent in link.parents:
        if getattr(parent, "name", None) not in {"article", "div", "li"}:
            continue
        classes = " ".join(parent.get("class", []))
        if any(token in classes for token in ("js__card", "re__card", "product-item")):
            return parent

    parent = link
    for _ in range(7):
        parent = parent.parent
        if parent is None:
            break
        text = parent.get_text(" ", strip=True)
        if re.search(r"(triệu|tr|nghìn|ngàn)\s*/?\s*tháng", text, re.IGNORECASE):
            return parent
    return link.parent


def parse_rental_listings(
    html: str,
    property_type: str = "phong_tro",
) -> list[RentalListing]:
    """Phân tích HTML công khai của trang kết quả Batdongsan.com.vn."""
    if "Just a moment" in html or "cf-chl-" in html:
        raise RentalSearchError(
            "Batdongsan.com.vn đang yêu cầu xác minh trình duyệt (Cloudflare). "
            "Tool không tự động vượt CAPTCHA; hãy thử lại chậm hơn hoặc mở URL nguồn."
        )

    soup = BeautifulSoup(html, "html.parser")
    links = soup.select(
        "a.js__product-link-for-product-id[href], "
        "a[href*='-pr'][href], "
        "a[data-product-id][href]"
    )
    results: list[RentalListing] = []
    seen_urls: set[str] = set()

    for link in links:
        href = link.get("href", "").strip()
        if not href or not re.search(r"-pr\d+", href, flags=re.IGNORECASE):
            continue

        url = urljoin(BATDONGSAN_BASE_URL, href.split("?")[0])
        if url in seen_urls:
            continue
        seen_urls.add(url)

        card = _listing_container(link)
        card_text = card.get_text(" ", strip=True)
        title = (
            link.get("title", "").strip()
            or _first_text(
                card,
                (
                    ".js__card-title",
                    ".re__card-title",
                    "[class*='card-title']",
                    "h3",
                ),
            )
            or link.get_text(" ", strip=True)
        )
        price, price_value = _parse_price(
            _first_text(
                card,
                (
                    ".re__card-config-price",
                    "[class*='config-price']",
                    "[class*='price']",
                ),
            )
            or card_text
        )
        area_text = _first_text(
            card,
            (
                ".re__card-config-area",
                "[class*='config-area']",
                "[class*='area']",
            ),
        )
        location = _first_text(
            card,
            (
                ".re__card-location",
                "[class*='card-location']",
                "[class*='location']",
            ),
        )
        description = _first_text(
            card,
            (
                ".re__card-description",
                "[class*='card-description']",
                "[class*='description']",
            ),
        )
        posted_at = _first_text(
            card,
            (
                ".re__card-published-info-published-at",
                "[class*='published-at']",
                "time",
            ),
        )
        results.append(
            RentalListing(
                title=title,
                price=price,
                price_million_per_month=price_value,
                area_m2=_parse_area(area_text or card_text),
                location=location,
                description=description[:500],
                posted_at=posted_at,
                url=url,
                verified="xác thực" in _plain_text(card_text),
                property_type=property_type,
            )
        )
    return results


def _normalize_property_type(value: str) -> str:
    normalized = _plain_text(value).replace("-", "_").replace(" ", "_")
    aliases = {
        "phong_tro": "phong_tro",
        "nha_tro": "phong_tro",
        "phong": "phong_tro",
        "can_ho": "can_ho",
        "chung_cu": "can_ho",
        "apartment": "can_ho",
        "tat_ca": "tat_ca",
        "all": "tat_ca",
    }
    if normalized not in aliases:
        raise ValueError(
            "property_type phải là 'phong_tro', 'can_ho' hoặc 'tat_ca'."
        )
    return aliases[normalized]


def _validate_range(name: str, minimum: Optional[float], maximum: Optional[float]):
    if minimum is not None and minimum < 0:
        raise ValueError(f"{name} tối thiểu không được âm.")
    if maximum is not None and maximum < 0:
        raise ValueError(f"{name} tối đa không được âm.")
    if minimum is not None and maximum is not None and minimum > maximum:
        raise ValueError(f"{name} tối thiểu không được lớn hơn tối đa.")


def search_rentals_data(
    location: str = "",
    keyword: str = "",
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_area: Optional[float] = None,
    max_area: Optional[float] = None,
    property_type: str = "phong_tro",
    limit: int = 10,
    pages: int = 1,
    timeout: int = 15,
    session: Optional[requests.Session] = None,
) -> dict:
    """
    Tìm tin cho thuê tại Hà Nội trên Batdongsan.com.vn.

    Giá dùng đơn vị triệu đồng/tháng, diện tích dùng m². Tool chỉ đọc các
    trang danh sách công khai, giới hạn tối đa 3 trang và không vượt CAPTCHA.
    """
    property_type = _normalize_property_type(property_type)
    _validate_range("Giá", min_price, max_price)
    _validate_range("Diện tích", min_area, max_area)
    if not 1 <= limit <= 20:
        raise ValueError("limit phải nằm trong khoảng 1..20.")
    if not 1 <= pages <= 3:
        raise ValueError("pages phải nằm trong khoảng 1..3.")
    if timeout < 3 or timeout > 60:
        raise ValueError("timeout phải nằm trong khoảng 3..60 giây.")

    categories = (
        list(RENTAL_URLS) if property_type == "tat_ca" else [property_type]
    )
    client = session or requests.Session()
    client.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0 Safari/537.36"
            ),
            "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.7",
        }
    )

    collected: list[RentalListing] = []
    source_urls: list[str] = []
    warnings: list[str] = []
    for category in categories:
        base_url = RENTAL_URLS[category]
        for page in range(1, pages + 1):
            url = base_url if page == 1 else f"{base_url}/p{page}"
            source_urls.append(url)
            try:
                response = client.get(url, timeout=timeout)
                if response.status_code in {403, 429}:
                    raise RentalSearchError(
                        f"Website từ chối truy cập tự động (HTTP {response.status_code}). "
                        f"Bạn có thể mở trực tiếp: {url}"
                    )
                response.raise_for_status()
                listings = parse_rental_listings(response.text, category)
                if not listings:
                    warnings.append(
                        f"Không đọc được tin nào tại {url}; cấu trúc trang có thể đã thay đổi."
                    )
                collected.extend(listings)
            except (requests.RequestException, RentalSearchError) as exc:
                warnings.append(str(exc))
                break
            if page < pages:
                time.sleep(1.5)

    location_query = _plain_text(location)
    keyword_query = _plain_text(keyword)
    filtered: list[RentalListing] = []
    for item in collected:
        searchable = _plain_text(
            " ".join((item.title, item.location, item.description))
        )
        if location_query and location_query not in searchable:
            continue
        if keyword_query and keyword_query not in searchable:
            continue
        if min_price is not None and (
            item.price_million_per_month is None
            or item.price_million_per_month < min_price
        ):
            continue
        if max_price is not None and (
            item.price_million_per_month is None
            or item.price_million_per_month > max_price
        ):
            continue
        if min_area is not None and (
            item.area_m2 is None or item.area_m2 < min_area
        ):
            continue
        if max_area is not None and (
            item.area_m2 is None or item.area_m2 > max_area
        ):
            continue
        filtered.append(item)

    filtered.sort(
        key=lambda item: (
            item.price_million_per_month is None,
            item.price_million_per_month or float("inf"),
        )
    )
    payload = {
        "source": "batdongsan.com.vn",
        "source_urls": source_urls,
        "filters": {
            "location": location,
            "keyword": keyword,
            "min_price_million": min_price,
            "max_price_million": max_price,
            "min_area_m2": min_area,
            "max_area_m2": max_area,
            "property_type": property_type,
        },
        "count": min(len(filtered), limit),
        "results": [asdict(item) for item in filtered[:limit]],
        "warnings": list(dict.fromkeys(warnings)),
    }
    return payload


def search_rentals(
    location: str = "",
    keyword: str = "",
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_area: Optional[float] = None,
    max_area: Optional[float] = None,
    property_type: str = "phong_tro",
    limit: int = 10,
) -> str:
    """Bản trả về JSON để ReAct Agent có thể gọi trực tiếp."""
    try:
        result = search_rentals_data(
            location=location,
            keyword=keyword,
            min_price=min_price,
            max_price=max_price,
            min_area=min_area,
            max_area=max_area,
            property_type=property_type,
            limit=limit,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except (ValueError, RentalSearchError) as exc:
        return json.dumps(
            {"error": str(exc), "results": []},
            ensure_ascii=False,
            indent=2,
        )


