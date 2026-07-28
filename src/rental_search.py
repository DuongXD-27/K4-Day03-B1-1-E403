"""CLI tìm nhà trọ/căn hộ cho thuê trên Batdongsan.com.vn."""

import argparse
import json

try:
    from .tools import search_rentals_data
except ImportError:
    from tools import search_rentals_data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Tìm tin cho thuê tại Hà Nội từ Batdongsan.com.vn"
    )
    parser.add_argument("--location", default="", help="Quận/phường/đường")
    parser.add_argument("--keyword", default="", help="Tiện ích hoặc từ khóa")
    parser.add_argument("--min-price", type=float, help="Giá thấp nhất (triệu/tháng)")
    parser.add_argument("--max-price", type=float, help="Giá cao nhất (triệu/tháng)")
    parser.add_argument("--min-area", type=float, help="Diện tích thấp nhất (m²)")
    parser.add_argument("--max-area", type=float, help="Diện tích cao nhất (m²)")
    parser.add_argument(
        "--type",
        dest="property_type",
        choices=("phong_tro", "can_ho", "tat_ca"),
        default="phong_tro",
        help="Loại bất động sản",
    )
    parser.add_argument("--limit", type=int, default=10, help="Số kết quả (1-20)")
    parser.add_argument("--pages", type=int, default=1, help="Số trang đọc (1-3)")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        payload = search_rentals_data(
            location=args.location,
            keyword=args.keyword,
            min_price=args.min_price,
            max_price=args.max_price,
            min_area=args.min_area,
            max_area=args.max_area,
            property_type=args.property_type,
            limit=args.limit,
            pages=args.pages,
        )
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2))
        return 2

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["results"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
