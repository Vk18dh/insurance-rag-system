import urllib.request; import json; import sys; 
req = urllib.request.Request('http://localhost:8000/api/v1/query/ask', data=json.dumps({'query': 'What is the surrender value for the LIC policy?'}).encode('utf-8'), headers={'Content-Type': 'application/json'})
try:
  res = urllib.request.urlopen(req)
  print('Answer:', json.loads(res.read()))
except Exception as e:
  print('Query failed:', e)
