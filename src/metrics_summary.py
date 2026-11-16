import json

traces = json.load(open("data/advanced_test_traces.json", encoding="utf-8"))
latencies = [t.get("latency_ms", 0) for t in traces]
median_lat = sorted(latencies)[len(latencies)//2]
mean_lat = sum(latencies) / len(latencies)
total_searches = sum(len(t.get("events", [])) - 1 for t in traces)

print(f"Total test cases: {len(traces)}")
print(f"Mean latency: {mean_lat:.1f} ms ({mean_lat/1000:.2f} s)")
print(f"Median latency: {median_lat:.1f} ms ({median_lat/1000:.2f} s)")
print(f"Total search calls: {total_searches}")
