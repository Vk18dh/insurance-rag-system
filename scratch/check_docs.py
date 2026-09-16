import requests

# Login
login_res = requests.post('http://localhost:8000/api/v1/auth/login', data={'username': 'admin', 'password': 'admin_password'})
token = login_res.json()['access_token']

# Query
query_data = {'query': 'What is the surrender value for the LIC policy?'}
query_res = requests.post('http://localhost:8000/api/v1/query', headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}, json=query_data)
print(query_res.json())
