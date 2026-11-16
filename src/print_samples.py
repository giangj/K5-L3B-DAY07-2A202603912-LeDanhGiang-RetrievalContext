"""Print sample traces for report."""
import json

test_best = json.load(open("results/agent/chosen_best_test.json", encoding="utf-8"))
for t in test_best["traces"]:
    print(f"ID: {t['query_id']} | Status: {t['status']}")
    print(f"Q: {t['question']}")
    print(f"Answer: {t['answer']}")
    print(f"Citations: {t['citations']}")
    print("-" * 50)
