import os
import requests
import time

PDF_DIR = r"c:\Users\dhyan\Desktop\majorcode\data\pdfs"

def upload_all():
    print("Logging in...")
    login_res = requests.post('http://localhost:8000/api/v1/auth/login', data={'username': 'admin', 'password': 'admin'})
    token = login_res.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    print("Uploading PDFs...")
    for filename in os.listdir(PDF_DIR):
        if not filename.lower().endswith(".pdf"):
            continue
            
        file_path = os.path.join(PDF_DIR, filename)
        
        with open(file_path, "rb") as f:
            files = {"file": (filename, f, "application/pdf")}
            data = {
                "document_name": filename,
                "document_type": "policy",
                "source": "local",
                "version": "1.0"
            }
            print(f"Uploading {filename}...")
            res = requests.post('http://localhost:8000/api/v1/admin/documents', headers=headers, data=data, files=files)
            
            if res.status_code == 202:
                print(f"Successfully uploaded: {filename}")
            else:
                print(f"Failed to upload {filename}: {res.status_code} {res.text}")
                
        # Slight delay to not overwhelm the ingestion background tasks immediately
        time.sleep(2)
        
if __name__ == "__main__":
    upload_all()
