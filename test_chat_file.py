"""Quick test: POST /chat/ with multipart (file upload) for swarm."""
import requests

url = "http://localhost:8002/chat/"
with open("test_upload.txt", "rb") as f:
    data = {"message": "Summarize this file and what is the net profit?", "mode": "swarm", "include_trace": "true"}
    files = {"file": ("test_upload.txt", f, "text/plain")}
    r = requests.post(url, data=data, files=files, timeout=90)
print("Status:", r.status_code)
if r.status_code != 200:
    print("Response:", r.text[:500])
    exit(1)
j = r.json()
print("Output:", j.get("output", "")[:500])
print("Success:", j.get("success"))
trace = j.get("trace") or []
print("Trace (first 8):", [{"node": t.get("node"), "decision": t.get("decision"), "preview": t.get("result_preview") or t.get("answer_preview")} for t in trace[:8]])
