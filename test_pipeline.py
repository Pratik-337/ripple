import requests
import uuid
import time
import subprocess
import os

BASE_URL = "http://localhost:8000/api/v1"

def print_result(step, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    print(f"{status} | {step} | {detail}")

def run_tests():
    email = f"test_{uuid.uuid4().hex[:6]}@example.com"
    password = "SecurePassword123!"

    # 1. Register and Login
    requests.post(f"{BASE_URL}/auth/register", json={"display_name": "Test User", "email": email, "password": password})
    r_login = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    token = r_login.json().get("data", {}).get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Project
    proj_name = f"Test Pipeline {uuid.uuid4().hex[:4]}"
    p1 = requests.post(f"{BASE_URL}/projects", headers=headers, json={"name": proj_name})
    project_id = p1.json().get("data", {}).get("id")
    print(f"Created Project ID: {project_id}")

    # ==========================
    # FILE UPLOAD PIPELINE
    # ==========================
    
    # Step 1: Get presigned URLs
    file_content = b'function validateUser() { return true; }'
    
    r_url = requests.post(f"{BASE_URL}/files/upload-url", headers=headers, json={
        "project_id": project_id,
        "files": [
            {"name": "validateUser.ts", "size": len(file_content), "content_type": "text/plain"}
        ]
    })
    
    passed = r_url.status_code == 200 and isinstance(r_url.json().get("data"), list)
    print_result("POST /api/v1/files/upload-url", passed, f"Status: {r_url.status_code}")
    if not passed:
        print(r_url.text)
        return
        
    upload_data = r_url.json().get("data")[0]
    file_id = upload_data.get("file_id")
    upload_url = upload_data.get("upload_url")
    s3_key = upload_data.get("storage_key")
    
    print(f"Got Upload URL for file: {file_id}, key: {s3_key}")

    # Step 2: Upload directly to MinIO
    r_put = requests.put(upload_url, data=file_content, headers={"Content-Type": "text/plain"})
    passed = r_put.status_code == 200
    print_result("PUT to MinIO", passed, f"Status: {r_put.status_code}")

    # Step 3: Confirm the batch
    # The user asked for POST /api/v1/projects/{id}/files/confirm-batch
    r_confirm = requests.post(f"{BASE_URL}/projects/{project_id}/files/confirm-batch", headers=headers, json={
        "file_ids": [file_id]
    })
    passed = r_confirm.status_code == 200 or r_confirm.status_code == 202
    print_result("POST /projects/{id}/files/confirm-batch", passed, f"Status: {r_confirm.status_code}")
    if not passed:
        print(r_confirm.text)
        return

    # Wait for celery task
    print("Waiting 5 seconds for Celery task to process and parse AST...")
    time.sleep(5)

    # Step 5: Verify in database
    print("\nVerifying parsed_symbols in Postgres:")
    query = f"SELECT id, path, language, SUBSTRING(parsed_symbols::text, 1, 50) as symbols_preview FROM project_files WHERE project_id = '{project_id}';"
    
    cmd = [
        "docker", "exec", "ripple_postgres", 
        "psql", "-U", "ripple", "-d", "ripple", "-c", query
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("ERRORS:", result.stderr)
        
    # Also Check celery logs 
    print("\nCelery trailing logs:")
    try:
        celery_cmd = ["docker-compose", "logs", "--tail=20", "worker"]
        # wait we aren't using docker-compose for celery. Celery runs locally.
    except Exception:
        pass

if __name__ == "__main__":
    run_tests()
