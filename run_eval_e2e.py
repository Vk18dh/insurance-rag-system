import requests
import time

def main():
    # Login as admin
    r = requests.post('http://localhost:8000/api/v1/auth/login', data={'username': 'admin', 'password': 'admin'})
    if r.status_code != 200:
        print("Admin login failed:", r.status_code, r.text)
        return
    token = r.json()['access_token']
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    # Start Evaluation
    print("Starting evaluation...")
    r = requests.post('http://localhost:8000/api/v1/admin/evaluations', headers=headers)
    if r.status_code != 200:
        print("Start evaluation failed:", r.status_code, r.text)
        return
    
    run_id = r.json()['run_id']
    print(f"Evaluation started with ID: {run_id}")
    
    # Poll for completion
    while True:
        r = requests.get(f'http://localhost:8000/api/v1/admin/evaluations/{run_id}', headers=headers)
        data = r.json()
        status = data.get('status')
        print(f"Status: {status}")
        if status in ['COMPLETED', 'FAILED']:
            print("Evaluation finished!")
            print(f"Overall Score: {data.get('overall_score')}")
            print(f"Total Cases: {data.get('total_cases')}")
            break
        time.sleep(5)

if __name__ == "__main__":
    main()
