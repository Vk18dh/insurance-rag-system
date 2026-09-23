import os
import sys
import requests
import time
from dotenv import load_dotenv

load_dotenv()

def register_and_login():
    # Attempt login
    url = 'http://localhost:8000/api/v1/auth/login'
    data = {'username': 'expert@example.com', 'password': 'expert'}
    r = requests.post(url, data=data)
    if r.status_code == 200:
        return r.json()['access_token']
    
    # If login fails, register
    print("Registering expert user...")
    r = requests.post('http://localhost:8000/api/v1/auth/register', json={
        'username': 'expert@example.com',
        'password': 'expert',
        'full_name': 'Expert User'
    })
    print(f"Register status: {r.status_code}")
    
    r = requests.post(url, data=data)
    if r.status_code == 200:
        return r.json()['access_token']
    
    raise Exception(f"Auth failed: {r.status_code} {r.text}")

def main():
    token = register_and_login()
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    query = "Explain the exact maturity benefit under LIC Bima Jyoti policy and under what conditions it is not payable"
    print(f"\nSending query: {query}")
    start = time.time()
    r = requests.post('http://localhost:8000/api/v1/query', json={'query': query}, headers=headers)
    elapsed = time.time() - start
    
    print(f"Elapsed: {elapsed:.2f}s")
    print(f"Status: {r.status_code}")
    print(r.json())

if __name__ == "__main__":
    main()
