"""Generate Advanced Benchmark (48 questions: 18 Dev + 30 Test) for Vinamilk Annual Report 2025."""
import json
from pathlib import Path

# Dev questions (18 questions: 15 answerable + 3 unanswerable)
dev_questions = [
    # Table (3)
    {
        "id": "adv_dev_tbl_01",
        "split": "dev",
        "category": "Bảng",
        "question": "Theo Báo cáo kết quả hoạt động kinh doanh hợp nhất năm 2025 (Trang 109), Chi phí bán hàng và Chi phí quản lý doanh nghiệp của Vinamilk năm 2025 lần lượt là bao nhiêu triệu VND?",
        "ground_truth": "Chi phí bán hàng năm 2025 là 3.778.583 triệu VND và Chi phí quản lý doanh nghiệp là 1.864.451 triệu VND.",
        "gold_page": 109,
        "is_answerable": True,
        "reason": "Tra cứu số liệu từ Báo cáo kết quả hoạt động kinh doanh hợp nhất trang 109."
    },
    {
        "id": "adv_dev_tbl_02",
        "split": "dev",
        "category": "Bảng",
        "question": "Theo Báo cáo tình hình tài chính hợp nhất tại ngày 31/12/2025 (Trang 108), Vay ngắn hạn và Vay dài hạn của Vinamilk là bao nhiêu triệu VND?",
        "ground_truth": "Tại ngày 31/12/2025, Vay ngắn hạn là 9.393.737 triệu VND và Vay dài hạn là 62.908 triệu VND.",
        "gold_page": 108,
        "is_answerable": True,
        "reason": "Tra cứu mục Nợ phải trả trên bảng cân đối kế toán hợp nhất trang 108."
    },
    {
        "id": "adv_dev_tbl_03",
        "split": "dev",
        "category": "Bảng",
        "question": "Theo bảng các chỉ tiêu tài chính quan trọng giai đoạn 2021-2025 (Trang 11), Hệ số thanh toán nhanh của Vinamilk trong hai năm 2024 và 2025 lần lượt là bao nhiêu?",
        "ground_truth": "Hệ số thanh toán nhanh năm 2024 là 1,73 và năm 2025 là 1,59.",
        "gold_page": 11,
        "is_answerable": True,
        "reason": "Tra cứu bảng chỉ tiêu khả năng thanh toán trang 11."
    },
    # Diagram / Image (3)
    {
        "id": "adv_dev_diag_01",
        "split": "dev",
        "category": "Ảnh, sơ đồ",
        "question": "Theo Sơ đồ Cấu trúc tập đoàn Vinamilk (Trang 14), Vinamilk nắm giữ bao nhiêu phần trăm cổ phần tại Lao-Jagro Development XiengKhouang Co., Ltd.?",
        "ground_truth": "Vinamilk nắm giữ 92,07% cổ phần tại Lao-Jagro Development XiengKhouang Co., Ltd.",
        "gold_page": 14,
        "is_answerable": True,
        "reason": "Đọc tỷ lệ sở hữu công ty con ở nước ngoài từ sơ đồ cấu trúc tập đoàn trang 14."
    },
    {
        "id": "adv_dev_diag_02",
        "split": "dev",
        "category": "Ảnh, sơ đồ",
        "question": "Theo Sơ đồ cấu trúc tập đoàn Vinamilk (Trang 14), tỷ lệ sở hữu của Vinamilk tại Công ty Cổ phần Đường Việt Nam là bao nhiêu %?",
        "ground_truth": "Vinamilk sở hữu 65,0% cổ phần tại Công ty Cổ phần Đường Việt Nam.",
        "gold_page": 14,
        "is_answerable": True,
        "reason": "Tra cứu tỷ lệ sở hữu công ty con trong nước tại trang 14."
    },
    {
        "id": "adv_dev_diag_03",
        "split": "dev",
        "category": "Ảnh, sơ đồ",
        "question": "Theo Sơ đồ nhân sự chủ chốt HĐQT (Trang 15), ai giữ vị trí Chủ tịch Ủy ban Chiến lược và ai là Chủ tịch Ủy ban Lương thưởng?",
        "ground_truth": "Chủ tịch Ủy ban Chiến lược là bà Mai Kiều Liên, và Chủ tịch Ủy ban Lương thưởng là bà Tiêu Yến Trinh.",
        "gold_page": 15,
        "is_answerable": True,
        "reason": "Nhận diện chức danh các Chủ tịch Ủy ban trực thuộc HĐQT tại trang 15."
    },
    # Chart (3)
    {
        "id": "adv_dev_cht_01",
        "split": "dev",
        "category": "Biểu đồ",
        "question": "Theo Biểu đồ cột mốc lịch sử phát triển (Trang 7), vào năm 2013 Vinamilk đã đầu tư nắm giữ bao nhiêu % cổ phần của Công ty TNHH Bò sữa Thống Nhất Thanh Hóa?",
        "ground_truth": "Năm 2013, Vinamilk đã đầu tư nắm giữ 96,1% cổ phần của Công ty TNHH Bò sữa Thống Nhất Thanh Hóa.",
        "gold_page": 7,
        "is_answerable": True,
        "reason": "Đọc số liệu mốc sự kiện năm 2013 từ biểu đồ lịch sử phát triển trang 7."
    },
    {
        "id": "adv_dev_cht_02",
        "split": "dev",
        "category": "Biểu đồ",
        "question": "Theo bảng và chuỗi số liệu chỉ tiêu cơ cấu vốn giai đoạn 2021-2025 (Trang 11), Hệ số nợ/Tổng tài sản của Vinamilk năm 2025 là bao nhiêu %?",
        "ground_truth": "Hệ số nợ/Tổng tài sản năm 2025 của Vinamilk là 17,7%.",
        "gold_page": 11,
        "is_answerable": True,
        "reason": "Tra cứu chuỗi chỉ tiêu cơ cấu vốn trang 11."
    },
    {
        "id": "adv_dev_cht_03",
        "split": "dev",
        "category": "Biểu đồ",
        "question": "Theo chuỗi số liệu khả năng sinh lời (Trang 11), Hệ số Lợi nhuận sau thuế/Doanh thu thuần của Vinamilk năm 2025 đạt bao nhiêu %?",
        "ground_truth": "Hệ số LNST/Doanh thu thuần năm 2025 của Vinamilk đạt 14,8%.",
        "gold_page": 11,
        "is_answerable": True,
        "reason": "Tra cứu tỷ lệ biên lợi nhuận ròng trên doanh thu trang 11."
    },
    # Multi-hop (3)
    {
        "id": "adv_dev_mh_01",
        "split": "dev",
        "category": "Multi-hop",
        "question": "Kết hợp Báo cáo tài chính Trang 108 và Trang 109, Vốn chủ sở hữu của Vinamilk tại 31/12/2025 là bao nhiêu và Lợi nhuận trước thuế năm 2025 đạt bao nhiêu triệu VND?",
        "ground_truth": "Vốn chủ sở hữu tại 31/12/2025 là 35.569.652 triệu VND và Lợi nhuận trước thuế năm 2025 là 10.741.612 triệu VND.",
        "gold_page": 108,
        "is_answerable": True,
        "reason": "Kết hợp số liệu từ Bảng cân đối kế toán (trang 108) và Báo cáo kết quả kinh doanh (trang 109)."
    },
    {
        "id": "adv_dev_mh_02",
        "split": "dev",
        "category": "Multi-hop",
        "question": "Kết hợp Trang 14 và Trang 15, Tổng Giám đốc của Vinamilk là ai và Công ty có bao nhiêu xí nghiệp kho vận trực thuộc trong nước?",
        "ground_truth": "Tổng Giám đốc là bà Mai Kiều Liên và Vinamilk có 02 xí nghiệp kho vận trực thuộc trong nước tại Hà Nội và Tp. HCM.",
        "gold_page": 15,
        "is_answerable": True,
        "reason": "Kết hợp thông tin chức danh Tổng Giám đốc (trang 15) và số lượng xí nghiệp kho vận (trang 14)."
    },
    {
        "id": "adv_dev_mh_03",
        "split": "dev",
        "category": "Multi-hop",
        "question": "Kết hợp Báo cáo Ban Điều hành (Trang 49) và Báo cáo lãi lỗ (Trang 109), Vòng quay hàng tồn kho năm 2025 là bao nhiêu và Lợi nhuận từ hoạt động kinh doanh năm 2025 đạt bao nhiêu triệu VND?",
        "ground_truth": "Vòng quay hàng tồn kho năm 2025 là 5,98 và Lợi nhuận từ hoạt động kinh doanh năm 2025 đạt 9.886.163 triệu VND.",
        "gold_page": 49,
        "is_answerable": True,
        "reason": "Kết hợp chỉ số vòng quay tồn kho trang 49 và lợi nhuận HĐKD trang 109."
    },
    # Text (3)
    {
        "id": "adv_dev_txt_01",
        "split": "dev",
        "category": "Text",
        "question": "Theo văn bản công bố Tầm nhìn và Sứ mệnh (Trang 8), Tầm nhìn của Vinamilk được phát biểu như thế nào?",
        "ground_truth": "Tầm nhìn của Vinamilk là: “Trở thành biểu tượng niềm tin hàng đầu Việt Nam về sản phẩm dinh dưỡng và sức khỏe phục vụ cuộc sống con người”.",
        "gold_page": 8,
        "is_answerable": True,
        "reason": "Trích dẫn nguyên văn Tầm nhìn doanh nghiệp từ trang 8."
    },
    {
        "id": "adv_dev_txt_02",
        "split": "dev",
        "category": "Text",
        "question": "Theo báo cáo quản trị công ty (Trang 80), trang website của Vinamilk được duy trì bằng những ngôn ngữ nào?",
        "ground_truth": "Website của Vinamilk được duy trì bằng 02 ngôn ngữ là tiếng Việt và tiếng Anh.",
        "gold_page": 80,
        "is_answerable": True,
        "reason": "Tra cứu mục C.9 Trang website của Công ty trang 80."
    },
    {
        "id": "adv_dev_txt_03",
        "split": "dev",
        "category": "Text",
        "question": "Theo báo cáo quản trị công ty (Trang 87), cuộc họp của tám (08) thành viên HĐQT không điều hành trong năm 2025 được tổ chức vào ngày nào và ghi nhận tại biên bản họp số bao nhiêu?",
        "ground_truth": "Cuộc họp được tổ chức vào ngày 24/11/2025 và được ghi nhận tại Biên bản họp số 15/BB-CTS.HĐQT/2025.",
        "gold_page": 87,
        "is_answerable": True,
        "reason": "Tra cứu mục D.3.2/D.3.3 trang 87."
    },
    # Unanswerable (3)
    {
        "id": "adv_dev_abs_01",
        "split": "dev",
        "category": "Thiếu bằng chứng",
        "question": "Doanh thu xuất khẩu sữa chua sang sao Thổ của Vinamilk năm 2025 là bao nhiêu tỷ đồng?",
        "ground_truth": "KHONG_CO_THONG_TIN",
        "gold_page": None,
        "is_answerable": False,
        "reason": "Tài liệu hoàn toàn không có thông tin xuất khẩu sang sao Thổ."
    },
    {
        "id": "adv_dev_abs_02",
        "split": "dev",
        "category": "Thiếu bằng chứng",
        "question": "Tỷ phú Bill Gates hiện đang sở hữu bao nhiêu phần trăm cổ phần của Vinamilk theo báo cáo thường niên 2025?",
        "ground_truth": "KHONG_CO_THONG_TIN",
        "gold_page": None,
        "is_answerable": False,
        "reason": "Tài liệu không có thông tin về tỷ lệ sở hữu của Bill Gates."
    },
    {
        "id": "adv_dev_abs_03",
        "split": "dev",
        "category": "Thiếu bằng chứng",
        "question": "Giá bán niêm yết của một hộp sữa bột Dielac vào năm 2050 là bao nhiêu đồng?",
        "ground_truth": "KHONG_CO_THONG_TIN",
        "gold_page": None,
        "is_answerable": False,
        "reason": "Tài liệu không đưa ra dự báo giá sản phẩm đến năm 2050."
    }
]

# Test questions (30 questions: 24 answerable + 6 unanswerable)
test_questions = [
    # 1. Bảng (6)
    {
        "id": "adv_test_tbl_01",
        "split": "test",
        "category": "Bảng",
        "question": "Theo Báo cáo kết quả hoạt động kinh doanh hợp nhất năm 2025 (Trang 109), Doanh thu và Lợi nhuận gộp của Vinamilk năm 2025 đạt bao nhiêu triệu VND?",
        "ground_truth": "Doanh thu năm 2025 đạt 54.248.830 triệu VND và Lợi nhuận gộp đạt 15.542.110 triệu VND.",
        "gold_page": 109,
        "is_answerable": True,
        "reason": "Tra cứu Doanh thu và Lợi nhuận gộp từ bảng báo cáo lãi lỗ hợp nhất trang 109."
    },
    {
        "id": "adv_test_tbl_02",
        "split": "test",
        "category": "Bảng",
        "question": "Theo Báo cáo tình hình tài chính hợp nhất tại ngày 31/12/2025 (Trang 108), Tổng tài sản và Nợ phải trả của Vinamilk là bao nhiêu triệu VND?",
        "ground_truth": "Tổng tài sản tại ngày 31/12/2025 là 56.091.826 triệu VND và Nợ phải trả là 20.522.174 triệu VND.",
        "gold_page": 108,
        "is_answerable": True,
        "reason": "Tra cứu Tổng tài sản và Nợ phải trả trên bảng cân đối kế toán hợp nhất trang 108."
    },
    {
        "id": "adv_test_tbl_03",
        "split": "test",
        "category": "Bảng",
        "question": "Theo bảng các chỉ tiêu tài chính quan trọng giai đoạn 2021-2025 (Trang 11), Hệ số thanh toán ngắn hạn của Vinamilk trong hai năm 2024 và 2025 lần lượt là bao nhiêu?",
        "ground_truth": "Hệ số thanh toán ngắn hạn năm 2024 là 2,03 và năm 2025 là 1,96.",
        "gold_page": 11,
        "is_answerable": True,
        "reason": "Tra cứu bảng chỉ tiêu khả năng thanh toán trang 11."
    },
    {
        "id": "adv_test_tbl_04",
        "split": "test",
        "category": "Bảng",
        "question": "Theo bảng thù lao Hội đồng Quản trị năm 2025 (Trang 78), thù lao của Chủ tịch HĐQT Nguyễn Hạnh Phúc và Tổng Giám đốc Mai Kiều Liên lần lượt là bao nhiêu triệu đồng?",
        "ground_truth": "Thù lao năm 2025 của ông Nguyễn Hạnh Phúc là 3.261 triệu đồng và của bà Mai Kiều Liên là 1.898 triệu đồng.",
        "gold_page": 78,
        "is_answerable": True,
        "reason": "Tra cứu số liệu thù lao HĐQT năm 2025 trang 78."
    },
    {
        "id": "adv_test_tbl_05",
        "split": "test",
        "category": "Bảng",
        "question": "Theo Báo cáo của Ban Điều hành về đánh giá các hệ số tài chính chủ yếu (Trang 49), Vòng quay các khoản phải thu năm 2025 của Vinamilk là bao nhiêu so với năm 2024?",
        "ground_truth": "Vòng quay các khoản phải thu năm 2025 là 12.12 (hoặc 12,12), tăng so với mức 11,42 của năm 2024.",
        "gold_page": 49,
        "is_answerable": True,
        "reason": "So sánh vòng quay các khoản phải thu giữa năm 2024 và 2025 tại bảng trang 49."
    },
    {
        "id": "adv_test_tbl_06",
        "split": "test",
        "category": "Bảng",
        "question": "Theo bảng tình hình tham dự họp của Ủy ban Kiểm toán năm 2025 (Trang 85), tỷ lệ tham dự họp của ông Đỗ Lê Hùng và ông Alain Xavier Cany lần lượt là bao nhiêu?",
        "ground_truth": "Ông Đỗ Lê Hùng tham dự 8/8 cuộc họp đạt tỷ lệ 100%, còn ông Alain Xavier Cany tham dự 7/8 cuộc họp đạt tỷ lệ 87,5%.",
        "gold_page": 85,
        "is_answerable": True,
        "reason": "Tra cứu bảng thống kê số buổi và tỷ lệ tham dự họp UBKT năm 2025 trang 85."
    },

    # 2. Ảnh, sơ đồ (5)
    {
        "id": "adv_test_diag_01",
        "split": "test",
        "category": "Ảnh, sơ đồ",
        "question": "Theo Sơ đồ tổ chức và quản lý của công ty (Trang 13), các ủy ban trực thuộc Hội đồng Quản trị bao gồm những ủy ban nào?",
        "ground_truth": "Các ủy ban trực thuộc Hội đồng Quản trị gồm: Ủy ban Nhân sự, Ủy ban Chiến lược, Ủy ban Lương thưởng và Ủy ban Kiểm toán.",
        "gold_page": 13,
        "is_answerable": True,
        "reason": "Nhận diện 4 ủy ban trực thuộc HĐQT từ sơ đồ tổ chức công ty trang 13."
    },
    {
        "id": "adv_test_diag_02",
        "split": "test",
        "category": "Ảnh, sơ đồ",
        "question": "Theo Sơ đồ Cấu trúc tập đoàn Vinamilk (Trang 14), Vinamilk sở hữu bao nhiêu phần trăm cổ phần tại Driftwood Dairy Holdings Corporation và Angkor Dairy Products Co., Ltd.?",
        "ground_truth": "Vinamilk sở hữu 100% cổ phần tại Driftwood Dairy Holdings Corporation và 100% tại Angkor Dairy Products Co., Ltd.",
        "gold_page": 14,
        "is_answerable": True,
        "reason": "Đọc tỷ lệ sở hữu tại 2 công ty con nước ngoài từ sơ đồ trang 14."
    },
    {
        "id": "adv_test_diag_03",
        "split": "test",
        "category": "Ảnh, sơ đồ",
        "question": "Theo Sơ đồ cấu trúc tập đoàn Vinamilk (Trang 14), Vinamilk có bao nhiêu nhà máy sản xuất sữa và bao nhiêu chi nhánh văn phòng bán hàng trực thuộc trong nước?",
        "ground_truth": "Vinamilk có 13 nhà máy sản xuất sữa tại Bắc, Trung, Nam và 03 chi nhánh văn phòng bán hàng tại Hà Nội, Đà Nẵng và Cần Thơ.",
        "gold_page": 14,
        "is_answerable": True,
        "reason": "Đọc số lượng nhà máy sản xuất sữa và chi nhánh văn phòng bán hàng từ sơ đồ cấu trúc tập đoàn trang 14."
    },
    {
        "id": "adv_test_diag_04",
        "split": "test",
        "category": "Ảnh, sơ đồ",
        "question": "Theo Sơ đồ nhân sự chủ chốt HĐQT (Trang 15), ông Alain Xavier Cany và bà Đặng Thị Thu Hà giữ vai trò thành viên tại những ủy ban nào trực thuộc HĐQT?",
        "ground_truth": "Ông Alain Xavier Cany là thành viên Ủy ban Chiến lược và Ủy ban Kiểm toán; bà Đặng Thị Thu Hà là thành viên Ủy ban Kiểm toán và Ủy ban Lương thưởng.",
        "gold_page": 15,
        "is_answerable": True,
        "reason": "Đọc vị trí kiêm nhiệm ủy ban của thành viên HĐQT từ sơ đồ nhân sự trang 15."
    },
    {
        "id": "adv_test_diag_05",
        "split": "test",
        "category": "Ảnh, sơ đồ",
        "question": "Theo Sơ đồ tổ chức và quản lý (Trang 13), Phòng Kiểm toán nội bộ báo cáo trực tiếp và báo cáo chức năng tới cơ quan nào?",
        "ground_truth": "Phòng Kiểm toán nội bộ báo cáo theo chức năng tới Ủy ban Kiểm toán thuộc Hội đồng Quản trị.",
        "gold_page": 13,
        "is_answerable": True,
        "reason": "Nhận diện tuyến báo cáo của Phòng Kiểm toán nội bộ trên sơ đồ trang 13."
    },

    # 3. Biểu đồ (5)
    {
        "id": "adv_test_cht_01",
        "split": "test",
        "category": "Biểu đồ",
        "question": "Theo Biểu đồ cột mốc lịch sử phát triển của Vinamilk (Trang 7), năm 1976 Vinamilk được thành lập với tên gọi gì và tiếp quản những nhà máy nào?",
        "ground_truth": "Năm 1976 Vinamilk được thành lập với tên gọi Công ty Sữa – Cà Phê Miền Nam, tiếp quản 03 nhà máy sữa Thống Nhất, Trường Thọ và sữa bột Dielac.",
        "gold_page": 7,
        "is_answerable": True,
        "reason": "Đọc thông tin cột mốc thành lập năm 1976 từ biểu đồ lịch sử trang 7."
    },
    {
        "id": "adv_test_cht_02",
        "split": "test",
        "category": "Biểu đồ",
        "question": "Theo chuỗi số liệu cơ cấu vốn giai đoạn 2021-2025 (Trang 11), Hệ số nợ/Tổng tài sản của Vinamilk năm nào đạt mức thấp nhất và giá trị là bao nhiêu?",
        "ground_truth": "Hệ số nợ/Tổng tài sản đạt mức thấp nhất vào năm 2022 với giá trị là 10,2%.",
        "gold_page": 11,
        "is_answerable": True,
        "reason": "So sánh và xác định năm có hệ số nợ/tổng tài sản thấp nhất từ bảng/chuỗi số liệu trang 11."
    },
    {
        "id": "adv_test_cht_03",
        "split": "test",
        "category": "Biểu đồ",
        "question": "Theo chuỗi số liệu chỉ tiêu khả năng sinh lời (Trang 11), tỷ suất sinh lời trên vốn chủ sở hữu (ROE) của Vinamilk trong năm 2025 đạt bao nhiêu % và tăng hay giảm so với năm 2024?",
        "ground_truth": "ROE năm 2025 đạt 27,3%, tăng so với mức 26,1% của năm 2024.",
        "gold_page": 11,
        "is_answerable": True,
        "reason": "Đọc và so sánh chỉ số ROE giữa năm 2024 và 2025 từ trang 11."
    },
    {
        "id": "adv_test_cht_04",
        "split": "test",
        "category": "Biểu đồ",
        "question": "Theo Biểu đồ lịch sử phát triển (Trang 7), vào năm 2003 sự kiện quan trọng nào đã diễn ra với Vinamilk?",
        "ground_truth": "Năm 2003, Vinamilk thực hiện cổ phần hóa và đổi tên thành Công ty Cổ phần Sữa Việt Nam.",
        "gold_page": 7,
        "is_answerable": True,
        "reason": "Đọc mốc sự kiện năm 2003 từ biểu đồ phát triển trang 7."
    },
    {
        "id": "adv_test_cht_05",
        "split": "test",
        "category": "Biểu đồ",
        "question": "Theo số liệu biến động Hệ số nợ/Vốn chủ sở hữu giai đoạn 2021-2025 (Trang 11), chỉ số này có xu hướng thay đổi như thế nào từ năm 2022 đến năm 2025?",
        "ground_truth": "Hệ số nợ/Vốn chủ sở hữu có xu hướng tăng liên tục từ 15,0% (năm 2022) lên 24,1% (năm 2023), 25,6% (năm 2024) và đạt 27,4% (năm 2025).",
        "gold_page": 11,
        "is_answerable": True,
        "reason": "Phân tích xu hướng biến động hệ số nợ/VCSH qua 4 năm từ trang 11."
    },

    # 4. Multi-hop (4)
    {
        "id": "adv_test_mh_01",
        "split": "test",
        "category": "Multi-hop",
        "question": "Kết hợp Báo cáo tài chính (Trang 109) và Thông điệp Tổng Giám đốc (Trang 5), chủ đề kỷ niệm năm 2025 của Vinamilk là gì và Doanh thu hợp nhất năm 2025 đạt bao nhiêu triệu VND?",
        "ground_truth": "Chủ đề kỷ niệm năm 2025 là '50 năm để tâm phụng sự' và Doanh thu hợp nhất năm 2025 đạt 54.248.830 triệu VND.",
        "gold_page": 109,
        "is_answerable": True,
        "reason": "Kết hợp chủ đề thông điệp kỷ niệm (trang 5) và số liệu doanh thu hợp nhất (trang 109)."
    },
    {
        "id": "adv_test_mh_02",
        "split": "test",
        "category": "Multi-hop",
        "question": "Kết hợp Trang 108 và Trang 109, Lợi nhuận gộp năm 2025 của Vinamilk là bao nhiêu và Tiền cùng các khoản tương đương tiền tại ngày 31/12/2025 là bao nhiêu triệu VND?",
        "ground_truth": "Lợi nhuận gộp năm 2025 là 15.542.110 triệu VND và Tiền cùng các khoản tương đương tiền tại ngày 31/12/2025 là 1.794.880 triệu VND.",
        "gold_page": 109,
        "is_answerable": True,
        "reason": "Kết hợp Lợi nhuận gộp từ báo cáo lãi lỗ (trang 109) và Tiền tương đương tiền từ bảng cân đối (trang 108)."
    },
    {
        "id": "adv_test_mh_03",
        "split": "test",
        "category": "Multi-hop",
        "question": "So sánh Bảng chỉ tiêu tài chính quan trọng (Trang 11) và Báo cáo tình hình tài chính hợp nhất (Trang 108), Tổng tài sản của Vinamilk tại 31/12/2025 là bao nhiêu và Vòng quay tổng tài sản năm 2025 đạt bao nhiêu?",
        "ground_truth": "Tổng tài sản tại ngày 31/12/2025 là 56.091.826 triệu VND và Vòng quay tổng tài sản năm 2025 là 1,17.",
        "gold_page": 108,
        "is_answerable": True,
        "reason": "Kết hợp Tổng tài sản (trang 108) và chỉ số Vòng quay tổng tài sản (trang 11)."
    },
    {
        "id": "adv_test_mh_04",
        "split": "test",
        "category": "Multi-hop",
        "question": "Kết hợp Sơ đồ nhân sự HĐQT (Trang 15) và Bảng thù lao HĐQT (Trang 78), Chủ tịch HĐQT là ai và nhận mức thù lao bao nhiêu triệu đồng trong năm 2025?",
        "ground_truth": "Chủ tịch HĐQT là ông Nguyễn Hạnh Phúc và nhận mức thù lao năm 2025 là 3.261 triệu đồng.",
        "gold_page": 78,
        "is_answerable": True,
        "reason": "Kết hợp chức danh Chủ tịch HĐQT (trang 15) và mức thù lao cá nhân (trang 78)."
    },

    # 5. Text (4)
    {
        "id": "adv_test_txt_01",
        "split": "test",
        "category": "Text",
        "question": "Theo văn bản công bố về Tầm nhìn và Sứ mệnh (Trang 8), Sứ mệnh cam kết của Vinamilk được phát biểu nguyên văn như thế nào?",
        "ground_truth": "Sứ mệnh của Vinamilk là: “Vinamilk cam kết mang đến cho cộng đồng nguồn dinh dưỡng tốt nhất, chất lượng nhất bằng chính sự trân trọng, tình yêu và trách nhiệm cao của mình với cuộc sống con người và xã hội”.",
        "gold_page": 8,
        "is_answerable": True,
        "reason": "Trích dẫn nguyên văn Sứ mệnh doanh nghiệp từ trang 8."
    },
    {
        "id": "adv_test_txt_02",
        "split": "test",
        "category": "Text",
        "question": "Theo công bố về Nhận diện các bên liên quan (Trang 9), đầu mối liên lạc của Công ty để quản lý quan hệ nhà đầu tư (IR) và Thư ký Công ty là những ai?",
        "ground_truth": "Đầu mối Ban Quan hệ nhà đầu tư là ông Trần Chí Sơn, và Thư ký Công ty là ông Lê Đức Anh.",
        "gold_page": 9,
        "is_answerable": True,
        "reason": "Tra cứu nhân sự đầu mối IR và Thư ký Công ty từ trang 9."
    },
    {
        "id": "adv_test_txt_03",
        "split": "test",
        "category": "Text",
        "question": "Theo Điều 11 Quy chế Nội bộ về Quản trị Công ty của Vinamilk (Trang 87), Hội đồng Quản trị phải họp với tần suất tối thiểu như thế nào?",
        "ground_truth": "HĐQT phải họp ít nhất mỗi quý một lần và có thể họp bất thường để thông qua quyết định bằng biểu quyết tại cuộc họp hoặc lấy ý kiến bằng văn bản.",
        "gold_page": 87,
        "is_answerable": True,
        "reason": "Tra cứu quy định tần suất họp định kỳ của HĐQT từ trang 87."
    },
    {
        "id": "adv_test_txt_04",
        "split": "test",
        "category": "Text",
        "question": "Theo quy định tại Điều 24.6 Điều lệ hoạt động của Vinamilk (Trang 87), thông báo mời họp Hội đồng Quản trị phải được gửi trước cho các thành viên ít nhất bao nhiêu ngày làm việc?",
        "ground_truth": "Thông báo mời họp Hội đồng Quản trị phải được gửi trước cho các thành viên Hội đồng Quản trị ít nhất năm (05) ngày làm việc trước khi tổ chức họp.",
        "gold_page": 87,
        "is_answerable": True,
        "reason": "Tra cứu thời hạn gửi thông báo mời họp HĐQT từ trang 87."
    },

    # 6. Thiếu bằng chứng (6)
    {
        "id": "adv_test_abs_01",
        "split": "test",
        "category": "Thiếu bằng chứng",
        "question": "Vinamilk dự kiến mở bao nhiêu showroom bán sữa tươi trực tiếp trên Mặt Trăng vào năm 2026?",
        "ground_truth": "KHONG_CO_THONG_TIN",
        "gold_page": None,
        "is_answerable": False,
        "reason": "Tài liệu hoàn toàn không có kế hoạch mở showroom trên Mặt Trăng."
    },
    {
        "id": "adv_test_abs_02",
        "split": "test",
        "category": "Thiếu bằng chứng",
        "question": "Theo báo cáo thường niên 2025, tỷ phú Elon Musk hiện đang nắm giữ bao nhiêu phần trăm cổ phần biểu quyết của Vinamilk?",
        "ground_truth": "KHONG_CO_THONG_TIN",
        "gold_page": None,
        "is_answerable": False,
        "reason": "Tài liệu không có thông tin Elon Musk nắm giữ cổ phần Vinamilk."
    },
    {
        "id": "adv_test_abs_03",
        "split": "test",
        "category": "Thiếu bằng chứng",
        "question": "Doanh thu thuần từ mảng bán điện thoại thông minh Vinamilk SmartMilk trong năm 2025 đạt bao nhiêu tỷ đồng?",
        "ground_truth": "KHONG_CO_THONG_TIN",
        "gold_page": None,
        "is_answerable": False,
        "reason": "Vinamilk không kinh doanh sản phẩm điện thoại thông minh."
    },
    {
        "id": "adv_test_abs_04",
        "split": "test",
        "category": "Thiếu bằng chứng",
        "question": "Vinamilk đã xây dựng bao nhiêu trang trại bò sữa tại Nam Cực tính đến cuối năm 2025?",
        "ground_truth": "KHONG_CO_THONG_TIN",
        "gold_page": None,
        "is_answerable": False,
        "reason": "Tài liệu không đề cập đến trang trại nào tại Nam Cực."
    },
    {
        "id": "adv_test_abs_05",
        "split": "test",
        "category": "Thiếu bằng chứng",
        "question": "Hạn chót để nộp hồ sơ xin cấp học bổng du học Sao Hỏa do Quỹ Vinamilk tài trợ năm 2025 là ngày nào?",
        "ground_truth": "KHONG_CO_THONG_TIN",
        "gold_page": None,
        "is_answerable": False,
        "reason": "Tài liệu không có chương trình học bổng sao Hỏa."
    },
    {
        "id": "adv_test_abs_06",
        "split": "test",
        "category": "Thiếu bằng chứng",
        "question": "Kế hoạch sáp nhập giữa Vinamilk và tập đoàn xe điện Tesla sẽ được triển khai vào quý nào của năm 2026?",
        "ground_truth": "KHONG_CO_THONG_TIN",
        "gold_page": None,
        "is_answerable": False,
        "reason": "Tài liệu không có kế hoạch sáp nhập với Tesla."
    }
]

all_questions = dev_questions + test_questions

# Format for questions.json
questions_data = {
    q["id"]: {
        "id": q["id"],
        "question": q["question"],
        "ground_truth": q["ground_truth"],
        "category": q["category"],
        "split": q["split"],
        "gold_page": q["gold_page"],
        "is_answerable": q["is_answerable"],
        "reason": q["reason"]
    }
    for q in all_questions
}

# Format for cases.json
cases_data = [
    {
        "id": q["id"],
        "question": q["question"],
        "expected_abstain": not q["is_answerable"],
        "expected_citations": [f"Trang {q['gold_page']}"] if q["is_answerable"] and q["gold_page"] else [],
        "ground_truth": q["ground_truth"],
        "category": q["category"],
        "split": q["split"]
    }
    for q in all_questions
]

with open("data/advanced_questions.json", "w", encoding="utf-8") as f:
    json.dump(questions_data, f, ensure_ascii=False, indent=2)

with open("data/advanced_cases.json", "w", encoding="utf-8") as f:
    json.dump(cases_data, f, ensure_ascii=False, indent=2)

print(f"Total benchmark questions created: {len(all_questions)}")
print(f"Dev questions: {len(dev_questions)} (Answerable: {sum(1 for q in dev_questions if q['is_answerable'])}, Unanswerable: {sum(1 for q in dev_questions if not q['is_answerable'])})")
print(f"Test questions: {len(test_questions)} (Answerable: {sum(1 for q in test_questions if q['is_answerable'])}, Unanswerable: {sum(1 for q in test_questions if not q['is_answerable'])})")

# Breakdown of Test set by category
cat_counts = {}
for q in test_questions:
    cat_counts[q["category"]] = cat_counts.get(q["category"], 0) + 1
print("Test set category breakdown:", cat_counts)
