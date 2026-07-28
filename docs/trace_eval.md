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
* **Thought 1**: Câu hỏi cần tra cứu thông tin thuê nhà.
* **Action 1**: `search_rentals['Hà Nội']`
* **Observation 1**: Tool trả về dữ liệu từ nguồn `batdongsan.com.vn` với bộ lọc khu vực Hà Nội.
* **Thought 2**: Agent cho rằng đã có thông tin thuê nhà và có thể tư vấn.
* **Final Answer**: *"Có nhiều phòng trọ ở Hà Nội phù hợp với yêu cầu của bạn!"*
* **Nhận xét**: Agent đã gọi tool nhưng truy vấn còn quá rộng (`Hà Nội` thay vì `Cầu Giấy`, ngân sách dưới 4 triệu, điều hòa, chỗ để xe). Câu trả lời cuối còn chung chung, chưa trích xuất rõ căn/phòng phù hợp từ Observation.
