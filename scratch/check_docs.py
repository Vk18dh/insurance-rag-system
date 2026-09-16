import requests
import json

# Login
login_res = requests.post('http://localhost:8000/api/v1/auth/login', data={'username': 'admin', 'password': 'admin'})
token = login_res.json()['access_token']

# Query
query_data = {'query': 'Are pre-existing conditions covered under the standard tier?'}
query_res = requests.post('http://localhost:8000/api/v1/query', headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}, json=query_data)
print(json.dumps(query_res.json(), indent=2))
