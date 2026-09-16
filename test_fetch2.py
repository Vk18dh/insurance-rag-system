import sys
from backend.app.services.auth_service import AuthService
from backend.app.schemas.auth import Role
auth = AuthService(None)
token = auth.create_access_token('admin', Role.ADMIN)
import urllib.request
req2 = urllib.request.Request('http://localhost:8000/api/v1/admin/documents', headers={'Authorization': 'Bearer ' + token})
try:
  res2 = urllib.request.urlopen(req2)
  print('Success:', res2.read().decode())
except Exception as e:
  print('Fetch failed:', e)
