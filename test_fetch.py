import urllib.request; import json; import sys; 
req = urllib.request.Request('http://localhost:8000/api/v1/auth/login', data=b'username=admin&password=dev_password', headers={'Content-Type': 'application/x-www-form-urlencoded'})
try:
  res = urllib.request.urlopen(req)
  token = json.loads(res.read())['access_token']
except Exception as e:
  print('Login failed:', e); sys.exit(1)

req2 = urllib.request.Request('http://localhost:8000/api/v1/admin/documents', headers={'Authorization': 'Bearer ' + token})
try:
  res2 = urllib.request.urlopen(req2)
  print('Docs:', len(json.loads(res2.read())))
except Exception as e:
  print('Fetch failed:', e)
