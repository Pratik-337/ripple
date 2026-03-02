import asyncio
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.component import ProjectFile, ComponentDependency

async def test_upload_pipeline():
    base = 'http://localhost:8000/api/v1'
    async with httpx.AsyncClient() as c:
        # Register user
        print("1. Register User / Login")
        u_creds = {'email': 'upload_master@ripple.com', 'password': 'p', 'display_name': 'Upload Master'}
        await c.post(f'{base}/auth/register', json=u_creds)
        l = await c.post(f'{base}/auth/login', json={'email': 'upload_master@ripple.com', 'password': 'p'})
        token = l.json()['data']['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Create proj
        print("2. Create Project")
        p = await c.post(f'{base}/projects', json={'name': 'Parser Test Proj'}, headers=headers)
        pid = p.json()['data']['id']
        
        # files to upload
        files_data = [
            {"name": "root.tsx", "size": 100, "content_type": "text/plain"},
            {"name": "utils.ts", "size": 50, "content_type": "text/plain"}
        ]
        
        print("3. Generate Upload URLs")
        u_res = await c.post(
            f"{base}/files/upload-url",
            json={"project_id": pid, "files": files_data},
            headers=headers
        )
        print("Upload URL Res:", u_res.status_code)
        
        f_list = u_res.json()["data"]
        file_ids = []
        
        print("4. Uploading to S3 Presigned URLs")
        for f_data in f_list:
            file_ids.append(f_data["file_id"])
            url = f_data["upload_url"]
            print(f"Uploading to {url[:40]}...")
            
            # Simple content that simulates a dependency
            content = b""
            if "utils.ts" in url:
                content = b"export const helper = () => true;"
            else:
                content = b"import { helper } from './utils';\nhelper();"
                
            put_res = await httpx.AsyncClient().put(url, content=content, headers={"Content-Type": "text/plain"})
            print("PUT Status:", put_res.status_code)
            
        print("5. Confirm Batch")
        c_res = await c.post(
            f"{base}/projects/{pid}/files/confirm-batch",
            json={"file_ids": file_ids},
            headers=headers
        )
        print("Confirm Status:", c_res.status_code)
        
        print("Waiting for celery background worker to run... (make sure it is running)")
        await asyncio.sleep(5) # Let Celery do its job

        # Check DB
        print("6. Verifying DB Parsing")
        async with AsyncSessionLocal() as session:
            res = await session.execute(select(ProjectFile).where(ProjectFile.project_id == pid))
            all_files = res.scalars().all()
            for pf in all_files:
                print(f"File {pf.path}: Confirmed={pf.confirmed}")
                if pf.parsed_symbols:
                    print("  Symbols extracted!")
                else:
                    print("  No symbols.")
                    
if __name__ == "__main__":
    asyncio.run(test_upload_pipeline())
