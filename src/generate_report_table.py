import json

reviews = json.load(open("data/advanced_test_reviews.json", encoding="utf-8"))
questions = json.load(open("data/advanced_questions.json", encoding="utf-8"))
traces = json.load(open("data/advanced_test_traces.json", encoding="utf-8"))
trace_map = {t["query_id"]: t for t in traces}

rows = []
for idx, r in enumerate(reviews, 1):
    qid = r["query_id"]
    q = questions[qid]
    t = trace_map[qid]
    
    cat = r["category"]
    q_txt = q["question"]
    tool_call = "search -> answer" if len(t.get("events", [])) > 1 else "answer"
    
    first_search = ""
    for e in t.get("events", []):
        if e.get("event") == "search":
            first_search = e.get("query", "")
            break
            
    ans = t.get("answer", "").replace("\n", " ")
    cits = t.get("citations", [])
    cit_str = ", ".join(cits) if cits else "[]"
    status_str = "**Đạt**" if r["passed"] else "**Chưa đạt**"
    note = r.get("note", "").replace("\n", " ")
    
    row = f"| `{qid}` | {cat} | {q_txt} | `{first_search}` | {ans} | `{cit_str}` | {status_str} ({note}) |"
    rows.append(row)

with open("data/report_test_table.md", "w", encoding="utf-8") as f:
    f.write("\n".join(rows))

print("Table generated with", len(rows), "rows.")
