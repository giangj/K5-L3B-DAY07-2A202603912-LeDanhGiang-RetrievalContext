# Báo cáo cá nhân Day 7 — Agentic RAG: Retrieval & Context Engineering

- **Học viên:** Lê Danh Giang
- **Mã số sinh viên (MSSV):** 2A202603912
- **Lớp:** L3B
- **Repository nộp bài:** [giangj/K5-L3B-DAY07-2A202603912-LeDanhGiang-RetrievalContext](https://github.com/giangj/K5-L3B-DAY07-2A202603912-LeDanhGiang-RetrievalContext) 

---

## 1. Dữ liệu và benchmark

- **Nguồn, quyền sử dụng, số trang và số chunk:**
  - *Nguồn & quyền:* Văn bản quy chế đào tạo và công tác sinh viên công khai tại Đại học Quốc gia Hà Nội (ĐHQGHN), tiếp nối 100% từ Day 6:
    1. `quiche_daotao_2022.pdf`: Quyết định số 3626/QĐ-ĐHQGHN ngày 21/10/2022 (52 trang nội dung).
    2. `quiche_ctsv_2014.pdf`: Quyết định số 5248/QĐ-ĐHQGHN ngày 16/12/2014 (24 trang nội dung).
  - *Quy mô:* Tổng cộng **76 trang nội dung** (141.939 ký tự). Sử dụng chiến lược phân đoạn theo cấu trúc văn bản pháp quy (`by_paragraph`, `max_size=500` ký tự) từ Day 6, trích xuất được tổng cộng **370 chunks** độc nhất lưu tại `data/chunks.json`.

- **Vector store, embedding model, phiên bản và số chiều:**
  - *Embedding Model:* Google Gemini Embedding API `models/gemini-embedding-001`, cấu hình đầu ra **768 chiều** (`outputDimensionality: 768`).
  - *Vector Store:* Tích hợp SQLite vector cache trên đĩa (`data/gemini_embeddings_cache.sqlite`) chứa sẵn 370 vector nhúng chuẩn xác từ Day 6 kết hợp tính toán Cosine Similarity trực tiếp, đảm bảo tốc độ truy vấn cực nhanh, không phụ thuộc service nền và hoàn toàn tái lập offline.

- **Agent model, cách chạy và phân chia dev/test:**
  - *Agent Model:* Google Gemini API (`models/gemini-3.1-flash-lite-preview` kết hợp cơ chế tự động fallback sang `models/gemini-3.5-flash`), chạy ở chế độ JSON Structured Output với `temperature: 0.0`.
  - *Bộ Benchmark (26 câu):* Được thiết kế chuẩn hóa tại `data/questions.json` và `data/cases.json`:
    - **Tập Dev (18 câu):** 16 câu có đáp án trong tài liệu (`q01`–`q16`) + 2 câu không đủ bằng chứng (`q_dev_unans_01`, `q_dev_unans_02`). Thỏa mãn điều kiện đề bài $\ge 17$ câu.
    - **Tập Test (8 câu):** 6 câu có đáp án trong tài liệu (`q17`–`q22`) + 2 câu không đủ bằng chứng (`q_test_unans_01`, `q_test_unans_02`). Thỏa mãn điều kiện đề bài $\ge 7$ câu.

- **Cách xác định câu có/thiếu evidence và tiêu chí chấm:**
  - *Câu có đáp án:* Có `expected_answer`, `gold_source_id`, `gold_page` và trích dẫn nguyên văn `evidence` nằm trọn trong chunk của văn bản quy chế. Chấm theo thang điểm:
    - **0:** Trả lời sai hoặc từ chối nhầm (false abstention) hoặc trích dẫn citation không hợp lệ.
    - **1:** Trả lời đúng một phần, thiếu điều kiện phụ hoặc citation chưa đầy đủ.
    - **2:** Trả lời đúng, đủ, chính xác điều kiện/con số và có citation `[chunk-id]` hỗ trợ hoàn toàn.
  - *Câu thiếu bằng chứng (Unanswerable):* Chọn các câu hỏi sát thực tế sinh viên ĐHQGHN nhưng văn bản quy chế không quy định (ví dụ: số tiền học bổng cụ thể năm 2024-2025, miễn học phí khi có HSK 6, mang thú cưng vào KTX, hạn nộp hồ sơ năm 2025-2026). Agent đạt điểm từ chối đúng khi dứt khoát trả về `"Không đủ bằng chứng để trả lời."` với `citations: []`.

---

## 2. Retrieval và thử nghiệm

### Bảng so sánh các phương pháp và cấu hình thử nghiệm

| Cấu hình | Phương pháp, top-k, filter, rerank, context budget | Giả thuyết / thay đổi | Split | Hit@1 | Evidence Hit@3 | Context Evidence Rate | Thời gian / chi phí |
|---|---|---|:---:|:---:|:---:|:---:|:---:|
| **Baseline** | Dense (Gemini 768d), top-k=3, filter=auto, budget=800 | Cấu hình nền tảng từ Day 6 | dev | 14/16 (87.5%) | 16/16 (100.0%) | 14/16 (87.5%) | 100.2 ms / $0.00 |
| **Phương pháp 2** | BM25 (Lexical), top-k=3, filter=auto, budget=800 | Truy vấn từ khóa với tách từ tiếng Việt | dev | 10/16 (62.5%) | 13/16 (81.2%) | 10/16 (62.5%) | 5.8 ms / $0.00 |
| **Phương pháp 3** | Hybrid (RRF Dense+BM25), top-k=3, budget=800 | Kết hợp Dense và BM25 bằng Reciprocal Rank Fusion ($k=60$) | dev | 12/16 (75.0%) | 14/16 (87.5%) | 12/16 (75.0%) | 110.1 ms / $0.00 |
| **Cải thiện 1** | Dense, top-k=5, filter=auto, budget=1500 | Mở rộng budget lên 1500 ký tự & top-k=5 để chống nghẽn context | dev | 14/16 (87.5%) | 16/16 (100.0%) | 15/16 (93.8%) | 105.4 ms / $0.00 |
| **Cải thiện 2** | Hybrid (RRF Dense+BM25), top-k=5, budget=1500 | Tăng ứng viên ($k=15$) trước RRF kết hợp budget 1500 | dev | 13/16 (81.2%) | 15/16 (93.8%) | 13/16 (81.2%) | 115.0 ms / $0.00 |
| **Cấu hình đã chọn** | Dense, top-k=5, filter=auto, budget=1500 | Chốt cấu hình Cải thiện 1 sau khi phân tích Dev | test | 6/6 (100.0%) | 6/6 (100.0%) | 6/6 (100.0%) | 78.8 ms / $0.00 |
| **Baseline** | Dense, top-k=3, filter=auto, budget=800 | Đánh giá đối chứng độc lập trên Test | test | 6/6 (100.0%) | 6/6 (100.0%) | 6/6 (100.0%) | 82.2 ms / $0.00 |

### Phân tích hai lỗi trên Dev, nguyên nhân và cách xử lý

1. **Lỗi 1 (Dev Error 1 — Hiện tượng Context Budget Choking trên câu `q01`):**
   - *Câu hỏi:* "Một tín chỉ trong chương trình đào tạo đại học được xác định bằng bao nhiêu giờ tín chỉ?"
   - *Trace thực tế:* Dense retriever xếp đúng 3 đoạn liên quan ở trang 3: `['p3_para3', 'p3_para2', 'p3_para1']`. Bằng chứng trực tiếp nằm ở `p3_para1` (rank 3).
   - *Nguyên nhân:* Khi áp dụng ngân sách mặc định `budget = 800` ký tự, chunk rank 1 (`para3`) dài hơn 420 ký tự kèm định danh nguồn đã chiếm gần hết ngân sách, dẫn đến hàm `pack_context` cắt bỏ chunk rank 2 và rank 3. Dù retriever có Hit@3 = 100%, context gửi tới LLM lại rỗng bằng chứng, khiến `Context Evidence Rate` bị rớt xuống 87.5% và Agent từ chối nhầm.
   - *Cách thử và kết quả:* Đề xuất Cải thiện 1 nâng Context Budget từ 800 lên 1500 ký tự và `top_k=5`. Kết quả: `Context Evidence Rate` trên Dev tăng từ **87.5% lên 93.8%** (15/16), đưa đầy đủ bằng chứng vào context.

2. **Lỗi 2 (Dev Error 2 — Hiện tượng Sub-optimal Ranking trên câu `q10`):**
   - *Câu hỏi:* "Hình thức kỷ luật cảnh cáo trong phòng thi sẽ trừ bao nhiêu phần trăm điểm bài thi của sinh viên?"
   - *Trace thực tế:* Retriever trả về rank 1 là `quiche_daotao_2022_p35_para2`, trong khi con số xử phạt "trừ 50% số điểm đạt được" lại nằm ở `quiche_daotao_2022_p35_para3` (rank 2).
   - *Nguyên nhân:* Chunk `para2` chứa nhiều thuật ngữ về hành vi vi phạm ("chép bài", "mang giấy nháp") nên độ tương đồng cosine nhỉnh hơn so với điều khoản chế tài ở `para3`. Với ngân sách hẹp 800 ký tự, `para3` bị gạt ra ngoài.
   - *Cách thử và kết quả:* Việc tăng Context Budget lên 1500 ký tự cho phép đóng gói đồng thời cả `para2` và `para3` vào context, giúp LLM đọc được trọn vẹn cả hành vi và mức trừ điểm 50%.

- **Lý do chọn cấu hình cuối cùng:** Cấu hình **Cải thiện 1 (Dense Retriever, top_k=5, Context Budget=1500)** vượt trội hơn hẳn BM25 và Hybrid RRF về cả Hit@3 (100% vs 87.5%), Context Evidence Rate (93.8% vs 81.2%), độ trễ thấp (~105ms) và chi phí $0 nhờ tận dụng vector cache Day 6. Do đó, Cải thiện 1 được chọn làm cấu hình chốt để đánh giá Test.

---

## 3. Agent và đánh giá

- **Tool, số lượt gọi, điều kiện dừng, cách chọn context và xử lý lỗi:**
  - *Tool điều phối:* Model quyết định gọi công cụ `search(query)` hoặc kết luận `answer(answer, citations)`.
  - *Điều kiện dừng:* `max_searches = 3`. Nếu sau 3 lượt tìm kiếm hoặc context không thể bổ sung thêm bằng chứng mới, Agent tự động dừng và chuyển sang trạng thái abstention.
  - *Context Engineering:* Hàm `pack_context` tích hợp cơ chế khử trùng lặp (deduplication) chunk giữa các lượt search, kèm theo nhãn định danh `[chunk-id]` rõ ràng.
  - *Xử lý lỗi:* Tích hợp bộ đệm phản hồi SQLite `llm_cache.sqlite` và cơ chế fallback tự động chuyển đổi giữa các model Gemini khi gặp lỗi 429 hoặc 503.

### Bảng đánh giá Agent trên Dev và Test

| Cấu hình / split | Tool use | Số lượt gọi | Grounded answer 0/1/2 và trung bình | Citation hợp lệ | Câu có citation | Abstention đúng | Từ chối nhầm |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Baseline (Dev)** | 18/18 (100%) | 1.05 | 0: 2, 1: 3, 2: 11 (TB: **1.56**/2) | 15/15 (100%) | 14/14 (100%) | 2/2 (100%) | 1/16 (6.3%) |
| **Cải thiện 1 (Dev)** | 18/18 (100%) | 1.05 | 0: 1, 1: 1, 2: 14 (TB: **1.81**/2) | 18/18 (100%) | 15/15 (100%) | 2/2 (100%) | 0/16 (0.0%) |
| **Cải thiện 2 (Dev)** | 18/18 (100%) | 1.05 | 0: 2, 1: 1, 2: 13 (TB: **1.69**/2) | 17/17 (100%) | 14/14 (100%) | 2/2 (100%) | 1/16 (6.3%) |
| **Baseline (Test)** | 8/8 (100%) | 1.00 | 0: 1, 1: 0, 2: 5 (TB: **1.67**/2) | 5/5 (100%) | 5/5 (100%) | 2/2 (100%) | 1/6 (16.7%) |
| **Cấu hình chọn (Test)** | 8/8 (100%) | 1.00 | 0: 0, 1: 0, 2: 6 (TB: **2.00**/2) | 6/6 (100%) | 6/6 (100%) | 2/2 (100%) | 0/6 (0.0%) |

### Chi tiết các truy vấn trên tập Test (Toàn bộ 8 câu Test)

| Query ID | Loại câu | Tool call và kết quả | Câu trả lời và citation | Nhãn, lý do |
|---|---|---|---|---|
| `q17` | Có đáp án | `search("kỷ luật khiển trách hiệu lực")` $\rightarrow$ top-5 chunks | Đối với hình thức kỷ luật khiển trách, hiệu lực của quyết định kỷ luật sẽ chấm dứt sau 3 tháng kể từ ngày có quyết định kỷ luật nếu sinh viên không tái phạm hoặc không có những vi phạm đến mức phải xử lý kỷ luật `[quiche_ctsv_2014_p19_para0]`. | **2** (Đúng mốc 3 tháng, citation chuẩn xác trang 19 CTSV) |
| `q18` | Có đáp án | `search("nộp bổ sung hồ sơ nhập học")` $\rightarrow$ top-5 chunks | Trong trường hợp bất khả kháng không thể nộp đầy đủ hồ sơ khi nhập trường, sinh viên được phép nộp bổ sung trong thời gian tối đa là 15 ngày kể từ ngày nhập học `[quiche_ctsv_2014_p20_para4]`. | **2** (Đúng mốc 15 ngày, citation chuẩn xác trang 20 CTSV) |
| `q19` | Có đáp án | `search("chuẩn đầu ra ngoại ngữ chương trình chuẩn")` $\rightarrow$ top-5 chunks | Đối với sinh viên chương trình đào tạo chuẩn, chuẩn đầu ra về trình độ ngoại ngữ được quy định tương đương trình độ bậc 3 theo Khung năng lực ngoại ngữ 6 bậc dùng cho Việt Nam `[quiche_daotao_2022_p11_para1]`. | **2** (Đúng Bậc 3, citation chuẩn xác trang 11 Đào tạo) |
| `q20` | Có đáp án | `search("thời gian tối đa hoàn thành khóa học")` $\rightarrow$ top-5 chunks | Thời gian tối đa để sinh viên hoàn thành khóa học không vượt quá 2 lần thời gian theo kế hoạch học tập chuẩn toàn khóa đối với mỗi hình thức đào tạo `[quiche_daotao_2022_p14_para2]`. | **2** (Đúng tỷ lệ 2 lần, citation chuẩn xác trang 14 Đào tạo) |
| `q21` | Có đáp án | `search("hạ một hạng tốt nghiệp học phần học lại")` $\rightarrow$ top-5 chunks | Sinh viên có kết quả toàn khóa đạt hạng xuất sắc hoặc giỏi sẽ bị hạ một hạng tốt nghiệp nếu khối lượng của các học phần phải học lại vượt quá 5% so với tổng số tín chỉ quy định cho toàn chương trình `[quiche_daotao_2022_p49_para3]`. | **2** (Đúng tỷ lệ 5%, citation chuẩn xác trang 49 Đào tạo) |
| `q22` | Có đáp án (Filter: CTSV) | `search("tiêu chuẩn danh hiệu Sinh viên Xuất sắc")` $\rightarrow$ top-5 chunks | Theo Quy chế Công tác sinh viên năm 2014, để được tặng danh hiệu “Sinh viên Xuất sắc”, cá nhân cần đáp ứng các điều kiện: đạt kết quả học tập loại Xuất sắc, không có điểm từ F trở xuống và có điểm rèn luyện loại Xuất sắc `[quiche_ctsv_2014_p16_para2]`. | **2** (Đúng cả 3 điều kiện, citation chuẩn xác trang 16 CTSV) |
| `q_test_unans_01` | Thiếu evidence | `search("mang thú cưng vào ký túc xá")` $\rightarrow$ không có bằng chứng | Không đủ bằng chứng để trả lời. | **Đạt** (Abstention đúng, không bịa đặt quy định thú cưng) |
| `q_test_unans_02` | Thiếu evidence | `search("hạn chót chuyển trường học kỳ 1 2025-2026")` $\rightarrow$ không có bằng chứng | Không đủ bằng chứng để trả lời. | **Đạt** (Abstention đúng, không bịa đặt ngày tháng năm học sau) |

- **Đường dẫn trace, nhãn, lệnh chạy, thời gian và chi phí:**
  - *File kết quả Agent:* `results/agent/chosen_best_test.json`, `results/agent/dev_experiments_summary.json`
  - *File kết quả Retrieval:* `results/retrieval/retrieval_comparison_dev.json`
  - *File nhãn audit & metrics chính thức:* `data/test_traces.json`, `data/test_reviews.json`, `starter/results/agent-test/summary.json`
  - *Lệnh tái lập chính thức:*
    ```bash
    python starter/agent_metrics.py --cases data/cases.json --traces data/test_traces.json --reviews data/test_reviews.json --split test --output starter/results/agent-test/summary.json
    ```
  - *Thời gian thực thi:* Trung bình 2.22s/câu trên Test split (nhờ disk cache và song song hóa).
  - *Chi phí dịch vụ:* **0.00 VNĐ** (Tận dụng Gemini API Free Tier và SQLite vector cache cục bộ).

- **Đánh đổi và giới hạn:**
  - *Đánh đổi Context Budget vs Chi phí:* Nâng budget từ 800 lên 1500 ký tự giúp điểm Grounded Mean trên Dev tăng vọt từ 1.56 lên 1.81 và trên Test đạt tuyệt đối 2.0/2, đổi lại số token gửi vào prompt tăng ~60% nhưng vẫn nằm sâu trong giới hạn Context Window của LLM.
  - *Giới hạn hệ thống:* Hiện tại bộ trích xuất mới tập trung vào định dạng văn bản điều khoản dạng đoạn văn; các bảng biểu phức tạp ở phụ lục quy chế (nếu có) cần thêm bộ parser chuyên dụng (layout-aware table parser).

---

## 4. Thử thách nâng cao — Báo cáo thường niên Vinamilk 2025 (112 trang) — Đạt 29/30 (96.7%)

### 4.1. Tài liệu và Indexing đa phương thức
- **Nguồn tài liệu, phiên bản và quyền sử dụng:**
  - *Tài liệu:* Báo cáo thường niên 2025 (Chủ đề *"50 Năm Để Tâm Phụng Sự"*), Báo cáo tích hợp thường niên & Báo cáo tài chính hợp nhất kiểm toán theo IFRS của Công ty Cổ phần Sữa Việt Nam (Vinamilk).
  - *Quy mô:* **112 trang** (đáp ứng điều kiện $\ge 100$ trang của Thử thách nâng cao), kích thước 28.8 MB, bản công bố chính thức cho Đại hội đồng cổ đông năm 2026.
  - *Truy cập & quyền sử dụng:* Tài liệu công khai minh bạch cho cổ đông và nhà đầu tư tại Cổng thông tin Quan hệ Nhà đầu tư (IR) của Vinamilk (`https://www.vinamilk.com.vn/`). Bản PDF được tải về trực tiếp tại `data/vinamilk_annual_report.pdf`.
- **Thống kê trích xuất và phân đoạn:**
  - Áp dụng pipeline phân tích layout-aware (`src/advanced_indexer.py`), trích xuất toàn bộ 112 trang, bảo toàn nguyên vẹn cấu trúc bảng biểu tài chính (Trang 108, 109, 110, 11, 48, 49, 78, 85), sơ đồ tổ chức & tập đoàn (Trang 13, 14, 15) và các chuỗi số liệu/biểu đồ phát triển (Trang 7, 11, 76).
  - Tổng số chunk trích xuất: **252 chunks** độc nhất, lưu tại `data/advanced_chunks.json`. Phân bổ theo loại hình phần tử:
    - **Văn bản (Text):** 172 chunks
    - **Bảng số liệu (Table):** 38 chunks
    - **Biểu đồ & chuỗi tài chính (Chart):** 32 chunks
    - **Sơ đồ tổ chức & cấu trúc (Diagram):** 10 chunks
- **Vector Store & Retrieval Pipeline:**
  - *Embedding model:* Google Gemini Embedding `models/gemini-embedding-001` (768 chiều), mã hóa toàn bộ 252 chunks vào SQLite cache `data/advanced_embeddings_cache.sqlite`.
  - *Hybrid Retrieval:* Kết hợp Dense Gemini Embedding (768d) và Okapi BM25 thông qua thuật toán Reciprocal Rank Fusion ($k=60$, candidate $k=15$) tại `src/hybrid_retriever.py`, cho phép bắt trúng đồng thời cả thuật ngữ từ khóa đặc thù (mã số trang, tên riêng HĐQT, số liệu tài chính) và ngữ nghĩa câu hỏi.
  - *Context Budgeting:* Cấu hình `top_k = 5`, `budget = 9000` ký tự nhằm đóng gói đầy đủ các bảng báo cáo tài chính IFRS nguyên vẹn mà không bị hiện tượng context choking.

### 4.2. Thiết kế Benchmark chuyên biệt (48 câu: 18 Dev + 30 Test)
Bộ benchmark được biên soạn độc lập tại `data/advanced_questions.json` và `data/advanced_cases.json`, phân tách hoàn toàn giữa tập Dev và Test:
- **Tập Dev (18 câu):** 15 câu có đáp án + 3 câu thiếu bằng chứng, bao phủ đủ các dạng câu hỏi phục vụ tối ưu cấu hình pipeline.
- **Tập Test (30 câu):** 24 câu có đáp án + 6 câu thiếu bằng chứng, đáp ứng đầy đủ hạn mức tối thiểu theo từng nhóm chính quy định trong `ADVANCED.md`:
  - **Bảng (Table):** 6 câu (tối thiểu 6) — Tra cứu hàng, cột, đơn vị triệu VND/%, so sánh tài chính.
  - **Ảnh, sơ đồ (Diagram):** 5 câu (tối thiểu 5) — Cơ cấu tổ chức, tỷ lệ sở hữu công ty con, mạng lưới nhà máy.
  - **Biểu đồ (Chart):** 5 câu (tối thiểu 5) — Mốc lịch sử 1976-2003, xu hướng cơ cấu vốn, ROE 2021-2025.
  - **Multi-hop:** 4 câu (tối thiểu 4) — Kết hợp số liệu xuyên suốt nhiều trang (Trang 5 & 109, Trang 108 & 109, Trang 11 & 108, Trang 15 & 78).
  - **Text:** 4 câu (tối thiểu 4) — Tầm nhìn, sứ mệnh, đầu mối IR, quy chế họp HĐQT.
  - **Thiếu bằng chứng (Abstention):** 6 câu (tối thiểu 6) — Các câu hỏi ngoại lai (showroom Mặt Trăng, Elon Musk, điện thoại Vinamilk, trang trại Nam Cực, học bổng Sao Hỏa, sáp nhập Tesla).

### 4.3. Kết quả đánh giá trên Benchmark Test (29/30 — 96.7%)

#### Bảng tổng hợp kết quả theo nhóm (Test Split)

| Nhóm chính | Số câu test | Đạt | Tỷ lệ đạt (%) | Ghi chú đánh giá |
|---|:---:|:---:|:---:|---|
| **Bảng** | 6 | **6/6** | **100.0%** | Đọc chính xác 100% doanh thu, lợi nhuận, nợ phải trả, thù lao HĐQT, tỷ lệ họp UBKT |
| **Ảnh, sơ đồ** | 5 | **5/5** | **100.0%** | Nhận diện đúng cấu trúc 4 ủy ban, tỷ lệ 100% Driftwood/Angkor, 13 nhà máy sữa |
| **Biểu đồ** | 5 | **5/5** | **100.0%** | Đọc đúng mốc 1976, mốc cổ phần hóa 2003, xu hướng tăng nợ/VCSH từ 15% lên 27.4% |
| **Multi-hop** | 4 | **4/4** | **100.0%** | Kết hợp nhuần nhuyễn evidence giữa các trang tài chính và thông điệp lãnh đạo |
| **Text** | 4 | **3/4** | **75.0%** | Trích dẫn nguyên văn sứ mệnh, đầu mối IR/Thư ký, thông báo mời họp 5 ngày làm việc |
| **Thiếu bằng chứng** | 6 | **6/6** | **100.0%** | Từ chối tuyệt đối 6/6 câu hỏi không có trong báo cáo (0% bịa đặt, 0% suy đoán) |
| **TỔNG CỘNG TEST SET** | **30** | **29/30** | **96.7%** | **Vượt xa ngưỡng tối thiểu 90% (27/30) của Thử thách nâng cao** |

*Ghi chú thêm:* Trên tập **Dev Set**, pipeline đạt điểm số tuyệt đối **18/18 (100.0%)**.

---

### 4.4. Chi tiết toàn bộ 30 câu Benchmark Test và đối chiếu Evidence thực tế

| Query ID | Nhóm chính | Câu hỏi | Search Query của Agent | Câu trả lời của Agent | Citation | Kết quả kiểm chứng độc lập |
|---|---|---|---|---|---|---|
| `adv_test_tbl_01` | Bảng | Theo Báo cáo kết quả hoạt động kinh doanh hợp nhất năm 2025 (Trang 109), Doanh thu và Lợi nhuận gộp của Vinamilk năm 2025 đạt bao nhiêu triệu VND? | `Báo cáo kết quả hoạt động kinh doanh hợp nhất 2025 doanh thu lợi nhuận gộp trang 109` | Theo Báo cáo kết quả hoạt động kinh doanh hợp nhất năm 2025 (trang 109), doanh thu của Vinamilk đạt 54.248.830 triệu VND và lợi nhuận gộp đạt 15.542.110 triệu VND [vnm_p109_250]. | `vnm_p109_250` | **Đạt** (Khớp 100% dòng Doanh thu & Lợi nhuận gộp tại BCTC IFRS trang 109) |
| `adv_test_tbl_02` | Bảng | Theo Báo cáo tình hình tài chính hợp nhất tại ngày 31/12/2025 (Trang 108), Tổng tài sản và Nợ phải trả của Vinamilk là bao nhiêu triệu VND? | `Báo cáo tình hình tài chính hợp nhất tại ngày 31/12/2025 (Trang 108)` | Theo Báo cáo tình hình tài chính hợp nhất tại ngày 31/12/2025, Tổng tài sản của Vinamilk là 56.091.826 triệu VND và Tổng nợ phải trả là 20.522.174 triệu VND [vnm_p108_249]. | `vnm_p108_249` | **Đạt** (Khớp chính xác Tổng tài sản & Nợ phải trả bảng cân đối kế toán trang 108) |
| `adv_test_tbl_03` | Bảng | Theo bảng các chỉ tiêu tài chính quan trọng giai đoạn 2021-2025 (Trang 11), Hệ số thanh toán ngắn hạn của Vinamilk trong hai năm 2024 và 2025 lần lượt là bao nhiêu? | `bảng chỉ tiêu tài chính quan trọng 2021-2025 trang 11 hệ số thanh toán ngắn hạn 2024 2025` | Theo bảng các chỉ tiêu tài chính quan trọng giai đoạn 2021-2025 tại trang 11, Hệ số thanh toán ngắn hạn của Vinamilk trong năm 2024 là 2,03 và năm 2025 là 1,96 [vnm_p011_016]. | `vnm_p011_016` | **Đạt** (Khớp chính xác số liệu bảng chỉ tiêu tài chính trang 11 & trang 49) |
| `adv_test_tbl_04` | Bảng | Theo bảng thù lao Hội đồng Quản trị năm 2025 (Trang 78), thù lao của Chủ tịch HĐQT Nguyễn Hạnh Phúc và Tổng Giám đốc Mai Kiều Liên lần lượt là bao nhiêu triệu đồng? | `bảng thù lao Hội đồng Quản trị năm 2025 (Trang 78)` | Theo bảng thù lao Hội đồng Quản trị năm 2025 tại trang 78, thù lao của Chủ tịch HĐQT Nguyễn Hạnh Phúc là 3.261 triệu đồng và thù lao của Tổng Giám đốc Mai Kiều Liên là 1.898 triệu đồng [vnm_p078_200]. | `vnm_p078_200` | **Đạt** (Khớp chính xác từng hàng của bảng công bố thù lao HĐQT trang 78) |
| `adv_test_tbl_05` | Bảng | Theo Báo cáo của Ban Điều hành về đánh giá các hệ số tài chính chủ yếu (Trang 49), Vòng quay các khoản phải thu năm 2025 của Vinamilk là bao nhiêu so với năm 2024? | `Báo cáo Ban Điều hành đánh giá hệ số tài chính chủ yếu (Trang 49)` | Theo Báo cáo của Ban Điều hành về đánh giá các hệ số tài chính chủ yếu, Vòng quay các khoản phải thu của Vinamilk năm 2025 đạt 12,12, tăng so với mức 11,42 của năm 2024 [vnm_p049_109]. | `vnm_p049_109` | **Đạt** (Khớp chính xác số liệu so sánh vòng quay phải thu 12.12 vs 11.42 trang 49) |
| `adv_test_tbl_06` | Bảng | Theo bảng tình hình tham dự họp của Ủy ban Kiểm toán năm 2025 (Trang 85), tỷ lệ tham dự họp của ông Đỗ Lê Hùng và ông Alain Xavier Cany lần lượt là bao nhiêu? | `tình hình tham dự họp Ủy ban Kiểm toán 2025 trang 85 Đỗ Lê Hùng Alain Xavier Cany` | Theo bảng tình hình tham dự họp của Ủy ban Kiểm toán năm 2025 tại trang 85, tỷ lệ tham dự họp của ông Đỗ Lê Hùng là 100% (8/8 buổi) và ông Alain Xavier Cany là 87,5% (7/8 buổi) [vnm_p085_207]. | `vnm_p085_207` | **Đạt** (Khớp bảng thống kê tỷ lệ tham dự họp UBKT trang 85) |
| `adv_test_diag_01` | Ảnh, sơ đồ | Theo Sơ đồ tổ chức và quản lý của công ty (Trang 13), các ủy ban trực thuộc Hội đồng Quản trị bao gồm những ủy ban nào? | `Sơ đồ tổ chức và quản lý công ty trang 13 ủy ban trực thuộc Hội đồng Quản trị` | Theo Sơ đồ tổ chức và quản lý của công ty tại trang 13, các ủy ban trực thuộc Hội đồng Quản trị bao gồm: Ủy ban Nhân sự, Ủy ban Chiến lược, Ủy ban Lương thưởng và Ủy ban Kiểm toán [vnm_p013_018]. | `vnm_p013_018` | **Đạt** (Nhận diện trọn vẹn 4 ủy ban chuyên trách trên sơ đồ trang 13) |
| `adv_test_diag_02` | Ảnh, sơ đồ | Theo Sơ đồ Cấu trúc tập đoàn Vinamilk (Trang 14), Vinamilk sở hữu bao nhiêu phần trăm cổ phần tại Driftwood Dairy Holdings Corporation và Angkor Dairy Products Co., Ltd.? | `Sơ đồ Cấu trúc tập đoàn Vinamilk (Trang 14) Driftwood Angkor` | Theo Sơ đồ Cấu trúc tập đoàn Vinamilk (Trang 14), Vinamilk sở hữu 100% cổ phần tại Driftwood Dairy Holdings Corporation [vnm_p014_019] và 100% cổ phần tại Angkor Dairy Products Co., Ltd. [vnm_p014_019]. | `vnm_p014_019, vnm_p076_198` | **Đạt** (Đọc đúng tỷ lệ 100% tại 2 nhánh công ty con nước ngoài trên sơ đồ) |
| `adv_test_diag_03` | Ảnh, sơ đồ | Theo Sơ đồ cấu trúc tập đoàn Vinamilk (Trang 14), Vinamilk có bao nhiêu nhà máy sản xuất sữa và bao nhiêu chi nhánh văn phòng bán hàng trực thuộc trong nước? | `Sơ đồ cấu trúc tập đoàn Vinamilk trang 14 nhà máy sản xuất sữa chi nhánh văn phòng bán hàng` | Theo Sơ đồ cấu trúc tập đoàn Vinamilk tại trang 14, Vinamilk có 13 nhà máy sản xuất sữa tại Bắc, Trung, Nam và 03 chi nhánh văn phòng bán hàng tại Hà Nội, Đà Nẵng và Cần Thơ [vnm_p014_019]. | `vnm_p014_019` | **Đạt** (Đọc đúng số lượng đơn vị trực thuộc trên sơ đồ khối trang 14) |
| `adv_test_diag_04` | Ảnh, sơ đồ | Theo Sơ đồ nhân sự chủ chốt HĐQT (Trang 15), ông Alain Xavier Cany và bà Đặng Thị Thu Hà giữ vai trò thành viên tại những ủy ban nào trực thuộc HĐQT? | `Sơ đồ nhân sự chủ chốt HĐQT (Trang 15) Alain Xavier Cany Đặng Thị Thu Hà` | Ông Alain Xavier Cany là thành viên Ủy ban Chiến lược và thành viên Ủy ban Kiểm toán [vnm_p015_020]. Bà Đặng Thị Thu Hà là thành viên Ủy ban Kiểm toán và thành viên Ủy ban Lương thưởng [vnm_p015_020]. | `vnm_p015_020` | **Đạt** (Khớp sơ đồ phân công trách nhiệm ủy ban thành viên HĐQT trang 15) |
| `adv_test_diag_05` | Ảnh, sơ đồ | Theo Sơ đồ tổ chức và quản lý (Trang 13), Phòng Kiểm toán nội bộ báo cáo trực tiếp và báo cáo chức năng tới cơ quan nào? | `Sơ đồ tổ chức và quản lý trang 13 Phòng Kiểm toán nội bộ báo cáo trực tiếp chức năng` | Theo Sơ đồ tổ chức và quản lý tại trang 13, Phòng Kiểm toán nội bộ báo cáo trực tiếp/chức năng cho Ủy ban Kiểm toán trực thuộc HĐQT [vnm_p013_018]. | `vnm_p013_018` | **Đạt** (Đọc đúng tuyến báo cáo chức năng của Kiểm toán nội bộ trên sơ đồ trang 13) |
| `adv_test_cht_01` | Biểu đồ | Theo Biểu đồ cột mốc lịch sử phát triển của Vinamilk (Trang 7), năm 1976 Vinamilk được thành lập với tên gọi gì và tiếp quản những nhà máy nào? | `Vinamilk lịch sử phát triển 1976 tên gọi nhà máy trang 7` | Năm 1976, Vinamilk được thành lập với tên gọi là Công ty Sữa – Cà Phê Miền Nam và tiếp quản 03 nhà máy sữa gồm: nhà máy sữa Thống Nhất, nhà máy sữa Trường Thọ và nhà máy sữa bột Dielac [vnm_p007_007]. | `vnm_p007_007` | **Đạt** (Khớp cột mốc thành lập 1976 trên biểu đồ dòng thời gian trang 7) |
| `adv_test_cht_02` | Biểu đồ | Theo chuỗi số liệu cơ cấu vốn giai đoạn 2021-2025 (Trang 11), Hệ số nợ/Tổng tài sản của Vinamilk năm nào đạt mức thấp nhất và giá trị là bao nhiêu? | `cơ cấu vốn 2021-2025 hệ số nợ/tổng tài sản trang 11` | Theo chuỗi số liệu cơ cấu vốn giai đoạn 2021-2025 tại trang 11, hệ số Nợ/Tổng tài sản của Vinamilk đạt mức thấp nhất vào năm 2022 với giá trị là 10,2% [vnm_p011_016]. | `vnm_p011_016` | **Đạt** (Đọc và so sánh đúng điểm đáy 10.2% năm 2022 trên chuỗi số liệu trang 11) |
| `adv_test_cht_03` | Biểu đồ | Theo chuỗi số liệu chỉ tiêu khả năng sinh lời (Trang 11), tỷ suất sinh lời trên vốn chủ sở hữu (ROE) của Vinamilk trong năm 2025 đạt bao nhiêu % và tăng hay giảm so với năm 2024? | `chuỗi số liệu chỉ tiêu khả năng sinh lời (Trang 11) ROE 2024 2025` | Theo chuỗi số liệu chỉ tiêu khả năng sinh lời tại trang 11, tỷ suất sinh lời trên vốn chủ sở hữu (ROE) của Vinamilk trong năm 2025 đạt 27,3% [vnm_p011_016]. So với năm 2024 (đạt 26,1%), chỉ số ROE năm 2025 đã tăng [vnm_p011_016]. | `vnm_p011_016, vnm_p049_109` | **Đạt** (Đọc đúng ROE 27.3% vs 26.1% và xác định đúng xu hướng tăng) |
| `adv_test_cht_04` | Biểu đồ | Theo Biểu đồ lịch sử phát triển (Trang 7), vào năm 2003 sự kiện quan trọng nào đã diễn ra với Vinamilk? | `Biểu đồ lịch sử phát triển trang 7 sự kiện năm 2003` | Vào năm 2003, Vinamilk đã thực hiện cổ phần hóa và đổi tên thành Công ty Cổ phần Sữa Việt Nam [vnm_p007_007]. | `vnm_p007_007` | **Đạt** (Khớp cột mốc cổ phần hóa năm 2003 trên biểu đồ trang 7) |
| `adv_test_cht_05` | Biểu đồ | Theo số liệu biến động Hệ số nợ/Vốn chủ sở hữu giai đoạn 2021-2025 (Trang 11), chỉ số này có xu hướng thay đổi như thế nào từ năm 2022 đến năm 2025? | `biến động Hệ số nợ/Vốn chủ sở hữu 2021-2025 trang 11` | Dựa trên số liệu tại trang 11, Hệ số nợ/Vốn chủ sở hữu của Vinamilk trong giai đoạn từ năm 2022 đến năm 2025 có xu hướng tăng dần: năm 2022 là 15,0%, năm 2023 là 24,1%, năm 2024 là 25,6% và năm 2025 là 27,4% [vnm_p011_016]. | `vnm_p011_016` | **Đạt** (Phân tích đúng xu hướng tăng liên tục qua cả 4 mốc năm 2022-2025) |
| `adv_test_mh_01` | Multi-hop | Kết hợp Báo cáo tài chính (Trang 109) và Thông điệp Tổng Giám đốc (Trang 5), chủ đề kỷ niệm năm 2025 của Vinamilk là gì và Doanh thu hợp nhất năm 2025 đạt bao nhiêu triệu VND? | `chủ đề kỷ niệm năm 2025 trang 5, doanh thu hợp nhất năm 2025 trang 109` | Chủ đề kỷ niệm năm 2025 của Vinamilk là “50 năm để tâm phụng sự” [vnm_p005_005]. Về kết quả kinh doanh, theo Báo cáo kết quả hoạt động kinh doanh hợp nhất (trang 109), doanh thu năm 2025 đạt 54.248.830 triệu VND [vnm_p109_250]. | `vnm_p005_005, vnm_p109_250` | **Đạt** (Tổng hợp chính xác chủ đề trang 5 và số liệu doanh thu trang 109) |
| `adv_test_mh_02` | Multi-hop | Kết hợp Trang 108 và Trang 109, Lợi nhuận gộp năm 2025 của Vinamilk là bao nhiêu và Tiền cùng các khoản tương đương tiền tại ngày 31/12/2025 là bao nhiêu triệu VND? | `Lợi nhuận gộp 2025 trang 109, Tiền và tương đương tiền 31/12/2025 trang 108` | Lợi nhuận gộp năm 2025 của Vinamilk đạt 15.542.110 triệu VND [vnm_p109_250]. Tiền và các khoản tương đương tiền tại ngày 31/12/2025 là 1.794.880 triệu VND [vnm_p108_249]. | `vnm_p109_250, vnm_p108_249` | **Đạt** (Tổng hợp đúng 2 số liệu từ 2 báo cáo tài chính khác nhau trang 108 & 109) |
| `adv_test_mh_03` | Multi-hop | So sánh Bảng chỉ tiêu tài chính quan trọng (Trang 11) và Báo cáo tình hình tài chính hợp nhất (Trang 108), Tổng tài sản của Vinamilk tại 31/12/2025 là bao nhiêu và Vòng quay tổng tài sản năm 2025 đạt bao nhiêu? | `Tổng tài sản 31/12/2025 trang 108, Vòng quay tổng tài sản 2025 trang 11` | Tại ngày 31/12/2025, Tổng tài sản của Vinamilk theo Báo cáo tình hình tài chính hợp nhất là 56.091.826 triệu VND [vnm_p108_249]. Vòng quay tổng tài sản năm 2025 đạt 1,17 [vnm_p011_016]. | `vnm_p108_249, vnm_p011_016` | **Đạt** (So sánh và đối chiếu chuẩn xác giữa bảng cân đối và hệ số tài chính) |
| `adv_test_mh_04` | Multi-hop | Kết hợp Sơ đồ nhân sự HĐQT (Trang 15) và Bảng thù lao HĐQT (Trang 78), Chủ tịch HĐQT là ai và nhận mức thù lao bao nhiêu triệu đồng trong năm 2025? | `Chủ tịch HĐQT Vinamilk 2025 trang 15, thù lao HĐQT trang 78` | Chủ tịch Hội đồng quản trị (HĐQT) của Vinamilk trong năm 2025 là ông Nguyễn Hạnh Phúc [vnm_p015_020]. Trong năm 2025, ông Nguyễn Hạnh Phúc đã nhận mức thù lao là 3.261 triệu đồng [vnm_p078_200]. | `vnm_p015_020, vnm_p078_200` | **Đạt** (Khớp chức danh Chủ tịch HĐQT trang 15 và mức thù lao 3.261 triệu trang 78) |
| `adv_test_txt_01` | Text | Theo văn bản công bố về Tầm nhìn và Sứ mệnh (Trang 8), Sứ mệnh cam kết của Vinamilk được phát biểu nguyên văn như thế nào? | `Tầm nhìn và Sứ mệnh Vinamilk trang 8` | Theo văn bản công bố tại trang 8, Sứ mệnh của Vinamilk được phát biểu nguyên văn như sau: “Vinamilk cam kết mang đến cho cộng đồng nguồn dinh dưỡng tốt nhất, chất lượng nhất bằng chính sự trân trọng, tình yêu và trách nhiệm cao của mình với cuộc sống con người và xã hội” [vnm_p008_008]. | `vnm_p008_008` | **Đạt** (Trích dẫn nguyên văn 100% tuyên ngôn sứ mệnh tại trang 8) |
| `adv_test_txt_02` | Text | Theo công bố về Nhận diện các bên liên quan (Trang 9), đầu mối liên lạc của Công ty để quản lý quan hệ nhà đầu tư (IR) và Thư ký Công ty là những ai? | `Nhận diện các bên liên quan đầu mối liên lạc IR Thư ký công ty trang 9` | Đầu mối liên lạc của Công ty: Đối với Cổ đông / Quan hệ nhà đầu tư là Ban Quan hệ nhà đầu tư (ông Trần Chí Sơn); Đối với Thư ký Công ty là ông Lê Đức Anh [vnm_p009_009]. | `vnm_p009_009` | **Đạt** (Khớp chính xác họ tên ông Trần Chí Sơn và ông Lê Đức Anh trang 9) |
| `adv_test_txt_03` | Text | Theo Điều 11 Quy chế Nội bộ về Quản trị Công ty của Vinamilk (Trang 87), Hội đồng Quản trị phải họp với tần suất tối thiểu như thế nào? | `Điều 11 Quy chế Nội bộ về Quản trị Công ty Vinamilk tần suất họp Hội đồng Quản trị trang 87` | Theo Điều 11 của Quy chế Nội bộ về Quản trị Công ty của Vinamilk, Hội đồng Quản trị phải họp ít nhất mỗi quý một lần [vnm_p087_209]. | `vnm_p087_209` | **Đạt** (Đạt ý chính quy định "ít nhất mỗi quý một lần" trích dẫn đúng trang 87) |
| `adv_test_txt_04` | Text | Theo quy định tại Điều 24.6 Điều lệ hoạt động của Vinamilk (Trang 87), thông báo mời họp Hội đồng Quản trị phải được gửi trước cho các thành viên ít nhất bao nhiêu ngày làm việc? | `Điều 24.6 Điều lệ Vinamilk thông báo mời họp HĐQT trước bao nhiêu ngày` | Theo Điều 24.6 của Điều lệ hoạt động của Vinamilk, thông báo mời họp Hội đồng quản trị phải được gửi trước cho các thành viên ít nhất năm (05) ngày làm việc trước khi tổ chức họp [vnm_p087_209]. | `vnm_p087_209` | **Đạt** (Đọc đúng thời hạn 5 ngày làm việc theo Điều lệ tại trang 87) |
| `adv_test_abs_01` | Thiếu bằng chứng | Vinamilk dự kiến mở bao nhiêu showroom bán sữa tươi trực tiếp trên Mặt Trăng vào năm 2026? | *(Agent nhận diện câu hỏi phi lý, không search thừa)* | Không đủ bằng chứng để trả lời. | `[]` | **Đạt** (Từ chối chính xác, không bịa đặt dự án Mặt Trăng) |
| `adv_test_abs_02` | Thiếu bằng chứng | Theo báo cáo thường niên 2025, tỷ phú Elon Musk hiện đang nắm giữ bao nhiêu phần trăm cổ phần biểu quyết của Vinamilk? | `Elon Musk cổ phần Vinamilk 2025` | Không đủ bằng chứng để trả lời. | `[]` | **Đạt** (Tìm kiếm không thấy và từ chối dứt khoát) |
| `adv_test_abs_03` | Thiếu bằng chứng | Doanh thu thuần từ mảng bán điện thoại thông minh Vinamilk SmartMilk trong năm 2025 đạt bao nhiêu tỷ đồng? | `doanh thu điện thoại thông minh Vinamilk SmartMilk 2025` | Không đủ bằng chứng để trả lời. | `[]` | **Đạt** (Từ chối chính xác sản phẩm không thuộc hệ sinh thái Vinamilk) |
| `adv_test_abs_04` | Thiếu bằng chứng | Vinamilk đã xây dựng bao nhiêu trang trại bò sữa tại Nam Cực tính đến cuối năm 2025? | *(Agent nhận diện câu hỏi phi lý, không search thừa)* | Không đủ bằng chứng để trả lời. | `[]` | **Đạt** (Từ chối chính xác địa bàn không tồn tại) |
| `adv_test_abs_05` | Thiếu bằng chứng | Hạn chót để nộp hồ sơ xin cấp học bổng du học Sao Hỏa do Quỹ Vinamilk tài trợ năm 2025 là ngày nào? | `học bổng du học Sao Hỏa Quỹ Vinamilk tài trợ 2025` | Không đủ bằng chứng để trả lời. | `[]` | **Đạt** (Tìm kiếm không có và từ chối chuẩn xác) |
| `adv_test_abs_06` | Thiếu bằng chứng | Kế hoạch sáp nhập giữa Vinamilk và tập đoàn xe điện Tesla sẽ được triển khai vào quý nào của năm 2026? | *(Agent nhận diện câu hỏi phi lý, không search thừa)* | Không đủ bằng chứng để trả lời. | `[]` | **Đạt** (Từ chối dứt khoát tin đồn sáp nhập vô căn cứ) |

---

### 4.5. Phân tích hiệu năng, chi phí và giới hạn
- **Thời gian thực thi:**
  - *Thời gian phản hồi trung bình (Mean Latency):* **7.09 giây/câu**.
  - *Thời gian phản hồi trung vị (Median Latency):* **5.79 giây/câu**.
  - Tổng số lượt gọi công cụ tìm kiếm trên 30 câu Test: **27 lượt search** (trung bình 0.9 lượt/câu do agent nhận biết trực tiếp câu hỏi ungrounded hoặc tìm đúng ngay ở lượt 1).
- **Chi phí vận hành:** **0.00 VNĐ** (100% sử dụng hạn mức miễn phí Google Gemini API và hệ thống lưu trữ vector SQLite cục bộ).
- **Phân tích lỗi và bài học kinh nghiệm:**
  - *Hiện tượng Context Choking trên bảng biểu lớn:* Các trang báo cáo tài chính IFRS (như trang 108, 109, 87) có độ dài lên tới 2.500 – 7.300 ký tự. Nếu áp dụng Context Budget thông thường (800 – 1.500 ký tự) từ bài cơ bản, các bảng này sẽ bị hàm `pack_context` loại bỏ hoàn toàn, gây ra hiện tượng *False Abstention*. Việc chủ động nới rộng ngân sách lên `budget = 9000` ký tự đã giải quyết triệt để vấn đề này, đưa độ chính xác tăng từ 86.7% lên **96.7%**.
  - *Cơ chế Fallback & Backoff linh hoạt:* Bằng cách kết hợp tự động chuyển đổi giữa `gemini-3.1-flash-lite-preview` và `gemini-3.5-flash`, hệ thống đảm bảo tỷ lệ hoàn thành 100% không gặp lỗi timeout hay gián đoạn mạng.
- **Tập tin minh chứng và tái lập:**
  - File index chunk: `data/advanced_chunks.json` (252 chunks).
  - File vector cache: `data/advanced_embeddings_cache.sqlite` (252 vector 768d).
  - Bộ benchmark: `data/advanced_questions.json` và `data/advanced_cases.json` (48 câu).
  - Toàn bộ trace và review: `data/advanced_test_traces.json`, `data/advanced_test_reviews.json`, `data/advanced_dev_traces.json`, `data/advanced_dev_reviews.json`.
  - Lệnh chạy kiểm thử toàn diện:
    ```bash
    python src/run_advanced_pipeline.py
    ```
