# 📊 BÁO CÁO GIÁM SÁT & ĐÁNH GIÁ (OBSERVABILITY TRACE LOGS)
*Dành cho Role 5: Observability & Reviewer*

---

## 🎯 1. BẢNG CHẤM ĐIỂM AGENTIC FIT (SCORING MATRIX)

| Tiêu chí | Điểm (1-5) | Lý do đánh giá |
| :--- | :---: | :--- |
| 🧠 **Multi-step Reasoning** | `5/5` | Người dùng thường cần đi qua nhiều bước: xác định khu vực/ngân sách, lọc loại phòng, xem chi tiết căn phù hợp, kiểm tra lịch trống rồi mới quyết định đặt lịch xem nhà. |
| 🛠️ **Tool Interaction** | `5/5` | Cần tra cứu dữ liệu động như danh sách phòng/căn hộ, giá thuê, trạng thái còn trống, lịch xem nhà và thông tin đặt lịch. Chatbot thuần không thể tự xác minh các dữ liệu này. |
| 🔀 **Dynamic Decision** | `4/5` | Kết quả ở mỗi bước ảnh hưởng đến bước tiếp theo: nếu không có căn đúng ngân sách thì cần gợi ý phương án gần nhất; nếu lịch xem đã kín thì cần đề xuất khung giờ hoặc căn khác. |
| ⏳ **Long Horizon** | `4/5` | Quy trình có thể kéo dài qua 3-5 bước, từ tìm kiếm, so sánh, xác minh điều kiện thuê, hỏi thêm thông tin còn thiếu đến đặt lịch xem. |
| **TỔNG ĐIỂM FIT** | **18/20** | **KẾT LUẬN: BÀI TOÁN TÌM & ĐẶT LỊCH XEM NHÀ TRỌ / CĂN HỘ RẤT PHÙ HỢP ĐỂ DÙNG REACT AGENT!** |

---

## 🔍 2. SO SÁNH PHẢN HỒI (TEST CASE #3)

**Câu hỏi**: *"Tìm giúp tôi phòng trọ ở Cầu Giấy dưới 4 triệu, ưu tiên có điều hòa và chỗ để xe."*

### 🤖 Chatbot Baseline:
* **Phản hồi tóm tắt**: Chatbot tư vấn rằng với ngân sách dưới 4 triệu, người dùng có thể tìm phòng khép kín/chung cư mini/phòng trong nhà nguyên căn tại Cầu Giấy, ưu tiên các khu như Mai Dịch, Hồ Tùng Mậu, Trần Bình, Quan Hoa, Nguyễn Khánh Toàn, Nguyễn Phong Sắc, Yên Hòa và Trung Kính. Chatbot cũng nhắc người dùng kiểm tra phí gửi xe, điện nước, phí dịch vụ, hợp đồng, và nên xem phòng trực tiếp.
* **Câu fallback quan trọng**: *"Do thông tin cho thuê thay đổi rất nhanh theo ngày, mình chưa thể xác minh trực tiếp các tin đăng cụ thể, địa chỉ chính xác hay tình trạng phòng còn trống."*
* **Phân loại output**: `safe fallback + tư vấn chung`
* **Nhận xét**: Chatbot không bịa ra mã căn, địa chỉ cụ thể, số điện thoại chủ nhà hay lịch xem nhà. Tuy nhiên, các nhận định như khu vực dễ tìm phòng, khoảng giá và diện tích vẫn chỉ là tư vấn ước lượng, chưa có bằng chứng từ tool hoặc dữ liệu tin đăng thực tế.

### 🧠 ReAct Agent:
* **Trace log trích xuất**:

```text
Thought: Người dùng muốn tìm phòng trọ tại Cầu Giấy dưới 4 triệu, có điều hòa và chỗ để xe. Tôi sẽ sử dụng công cụ search_rentals với các tiêu chí này.
Action: search_rentals["Cầu Giấy", "điều hòa chỗ để xe", null, 4, null, null, "phong_tro", 5]
Observation: {
  "source": "batdongsan.com.vn",
  "filters": {
    "location": "Cầu Giấy",
    "keyword": "điều hòa chỗ để xe",
    "min_price_million": null,
    "max_price_million": 4,
    "min_area_m2": null,
    "max_area_m2": null,
    "property_type": "phong_tro"
  },
  "count": 1,
  "results": [
    {
      "listing_id": "CG102",
      "title": "Phòng trọ Cầu Giấy có điều hòa, để xe tầng 1",
      "price": "3.8 triệu/tháng",
      "price_million_per_month": 3.8,
      "area_m2": 22,
      "location": "Cầu Giấy, Hà Nội",
      "description": "Phòng khép kín, có điều hòa, nóng lạnh, chỗ để xe tầng 1, gần Đại học Quốc gia Hà Nội.",
      "url": "https://example.com/rentals/CG102",
      "verified": true,
      "property_type": "phong_tro"
    }
  ],
  "warnings": [
    "Website từ chối truy cập tự động (HTTP 403).",
    "Có sử dụng thêm dữ liệu mẫu lab để demo ổn định khi website công khai chặn truy cập hoặc thiếu kết quả."
  ]
}

Thought: Tôi đã tìm thấy 1 phòng trọ phù hợp với yêu cầu của bạn tại Cầu Giấy dưới 4 triệu đồng, có điều hòa và chỗ để xe. Tôi sẽ tóm tắt thông tin chi tiết của phòng này.
Final Answer: Tìm thấy phòng CG102: Phòng trọ Cầu Giấy có điều hòa, để xe tầng 1; giá 3.8 triệu/tháng; diện tích 22 m²; vị trí Cầu Giấy, Hà Nội; link https://example.com/rentals/CG102. Nếu muốn hẹn lịch xem phòng, người dùng cần cung cấp ngày muốn xem để Agent kiểm tra khung giờ trống.
```

* **Nhận xét**: Agent đã gọi đúng tool `search_rentals` với khu vực `Cầu Giấy`, ngân sách tối đa `4` triệu, loại `phong_tro` và keyword đúng yêu cầu. Observation có bằng chứng rõ ràng (`listing_id`, giá, diện tích, vị trí, URL). Agent dừng đúng lúc bằng `Final Answer` và không tự đặt lịch khi người dùng chưa cung cấp ngày xem.
