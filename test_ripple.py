import requests
import json
import uuid

BASE_URL = "http://localhost:8000/api/v1"

def print_result(step, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    print(f"{status} | {step} | {detail}")

def run_tests():
    email = f"test_{uuid.uuid4().hex[:6]}@example.com"
    password = "SecurePassword123!"

    print("--- AUTH TESTS ---")
    
    # 1. Register
    r = requests.post(f"{BASE_URL}/auth/register", json={
        "display_name": "Test User",
        "email": email,
        "password": password
    })
    passed = r.status_code == 201
    print_result("POST /api/v1/auth/register", passed, f"Status: {r.status_code}")

    # 2. Register same email
    r2 = requests.post(f"{BASE_URL}/auth/register", json={
        "display_name": "Test User 2",
        "email": email,
        "password": password
    })
    passed = r2.status_code == 409
    print_result("POST /api/v1/auth/register (Same Email)", passed, f"Status: {r2.status_code}")

    # 3. Login wrong password
    r3 = requests.post(f"{BASE_URL}/auth/login", json={
        "email": email,
        "password": "WrongPassword!"
    })
    passed = r3.status_code == 401
    print_result("POST /api/v1/auth/login (Wrong Password)", passed, f"Status: {r3.status_code}")

    # 4. Login correct password
    r4 = requests.post(f"{BASE_URL}/auth/login", json={
        "email": email,
        "password": password
    })
    passed = r4.status_code == 200 and "access_token" in r4.json().get("data", {})
    token = r4.json().get("data", {}).get("access_token")
    cookies = r4.cookies
    print_result("POST /api/v1/auth/login (Correct)", passed, f"Status: {r4.status_code}")

    # 5. Get /auth/me
    # Need access token in header according to API
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    r5 = requests.get(f"{BASE_URL}/auth/me", headers=headers, cookies=cookies)
    passed = r5.status_code == 200
    print_result("GET /api/v1/auth/me (With Token)", passed, f"Status: {r5.status_code}")

    # 6. Logout
    r6 = requests.post(f"{BASE_URL}/auth/logout", headers=headers, cookies=cookies)
    passed = r6.status_code == 200
    print_result("POST /api/v1/auth/logout", passed, f"Status: {r6.status_code}")

    # 7. Get /auth/me after logout
    # Refresh token might be deleted, so request with no token to test unauthorized 
    r7 = requests.get(f"{BASE_URL}/auth/me", cookies=r6.cookies)
    passed = r7.status_code == 401
    print_result("GET /api/v1/auth/me (After Logout)", passed, f"Status: {r7.status_code}")

    if not token:
        print("Cannot proceed to Projects CRUD. Auth failed.")
        return

    print("\n--- PROJECTS CRUD ---")
    
    # Need to log back in to get a valid token for CRUD
    r_login = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    new_token = r_login.json().get("data", {}).get("access_token")
    headers = {"Authorization": f"Bearer {new_token}"}
    
    # 1. Create project
    proj_name = f"Test Project {uuid.uuid4().hex[:4]}"
    p1 = requests.post(f"{BASE_URL}/projects", headers=headers, json={
        "name": proj_name,
        "description": "A test project",
        "color": "blue",
        "icon": "Box"
    })
    passed = p1.status_code == 201
    print_result("POST /api/v1/projects", passed, f"Status: {p1.status_code}")
    if not passed:
        print("Response:", p1.text)
        return
        
    project_id = p1.json().get("data", {}).get("id")

    # 2. List projects
    p2 = requests.get(f"{BASE_URL}/projects", headers=headers)
    passed = p2.status_code == 200 and isinstance(p2.json().get("data"), list)
    print_result("GET /api/v1/projects", passed, f"Status: {p2.status_code}")
    if not passed:
        print("Response:", p2.text)

    # 3. Get project
    p3 = requests.get(f"{BASE_URL}/projects/{project_id}", headers=headers)
    passed = p3.status_code == 200
    print_result(f"GET /api/v1/projects/{project_id}", passed, f"Status: {p3.status_code}")

    # 4. Patch project
    p4 = requests.patch(f"{BASE_URL}/projects/{project_id}", headers=headers, json={
        "name": f"{proj_name} (Updated)"
    })
    passed = p4.status_code == 200 and p4.json().get("data", {}).get("name") == f"{proj_name} (Updated)"
    print_result(f"PATCH /api/v1/projects/{project_id}", passed, f"Status: {p4.status_code}")

    # 5. Confirm project
    p5 = requests.post(f"{BASE_URL}/projects/{project_id}/confirm", headers=headers)
    passed = p5.status_code == 200 and p5.json().get("data", {}).get("status") == "active"
    print_result(f"POST /api/v1/projects/{project_id}/confirm", passed, f"Status: {p5.status_code}")
    if not passed:
        print("Response:", p5.text)

if __name__ == "__main__":
    run_tests()
