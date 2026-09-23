import requests
import json
import uuid

def main():
    # Login as expert
    r = requests.post('http://localhost:8000/api/v1/auth/login', data={'username': 'expert', 'password': 'expert'})
    token = r.json()['access_token']
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    # Force create a ReviewTask by simulating a domain uncertainty exception?
    # No, we can just insert a ReviewTask directly into the DB using psycopg2, or trigger a HITL by sending an ambiguous query.
    # An ambiguous query is one that hits the Contradiction Agent with conflicting info, or hits Risk Agent with HIGH risk, or Ambiguity.
    query = "Does LIC Bima Jyoti have a guaranteed addition of 5000 per 1000 sum assured or 50 per 1000 sum assured?"
    print(f"Sending ambiguous query to trigger HITL: {query}")
    r = requests.post('http://localhost:8000/api/v1/query', json={'query': query}, headers=headers)
    print(r.status_code, r.text)

    # Fetch review tasks
    r = requests.get('http://localhost:8000/api/v1/expert/reviews', headers=headers)
    print("GET reviews status:", r.status_code)
    print("GET reviews response:", r.text)
    tasks = r.json()
    if r.status_code == 200 and len(tasks) > 0:
        task_id = tasks[0]['id']
        print(f"Resolving task {task_id}")
        r = requests.post(f'http://localhost:8000/api/v1/expert/reviews/{task_id}/action', json={
            'resolution_text': 'The guaranteed addition is Rs. 50 per 1000 Basic Sum Assured per year.',
            'action_taken': 'DOCUMENTATION_UPDATED',
            'trigger_reindex': True
        }, headers=headers)
        print(f"Resolve status: {r.status_code}")
        print(r.json())
        
if __name__ == "__main__":
    main()
