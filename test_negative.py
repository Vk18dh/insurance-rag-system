import urllib.request, json
data = json.dumps({'query':'What is the capital of France?'}).encode('utf-8')
req = urllib.request.Request('http://localhost:8000/api/v1/query', data=data, headers={'Content-Type':'application/json'})
try:
    resp = urllib.request.urlopen(req)
    d = json.loads(resp.read())
    print("Answer:", d.get("final_answer", ""))
    print("Confidence:", d.get("confidence_score"))
except Exception as e:
    print("Failed", e)
