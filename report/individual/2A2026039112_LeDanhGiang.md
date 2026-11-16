# Báo cáo cá nhân Day 7 — Agentic RAG: Retrieval & Context Engineering

- **Học viên:** Lê Danh Giang
- **Mã số sinh viên (MSSV):** 2A2026039112
- **Lớp:** L3B
- **Repository nộp bài:** [giangj/K5-L3B-DAY07-2A2026039112-LeDanhGiang-RetrievalContext](https://github.com/giangj/K5-L3B-DAY07-2A2026039112-LeDanhGiang-RetrievalContext)

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

## 4. Thử thách nâng cao (Không thực hiện)

Bài làm tập trung tối ưu hóa 100% chất lượng và tính khoa học của **Phần cơ bản (85 điểm)** theo đúng chiến lược kiểm chứng độc lập.
