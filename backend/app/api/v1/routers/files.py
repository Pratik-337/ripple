import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.component import ProjectFile, Component, ComponentContributor, FileDraft, ComponentDependency
from app.core.storage import generate_presigned_put_url, object_exists, generate_presigned_get_url, download_bytes
from sqlalchemy import update
from app.services.language_detector import detect_language
from app.tasks.parsing import parse_project

router = APIRouter(tags=["files"])

class FileUploadReq(BaseModel):
    name: str
    size: int
    content_type: str

class UploadBatchReq(BaseModel):
    project_id: str
    files: List[FileUploadReq]

class ConfirmBatchReq(BaseModel):
    file_ids: List[str]

@router.post("/files/upload-url")
async def generate_presigned_urls(req: UploadBatchReq, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Verify project access
    res = await db.execute(select(Project).where(Project.id == req.project_id))
    project = res.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only owner can upload files for now")

    response_data = []

    for fReq in req.files:
        unique_uuid = str(uuid.uuid4())
        s3_key = f"projects/{req.project_id}/{unique_uuid}/{fReq.name}"
        
        project_file = ProjectFile(
            project_id=req.project_id,
            path=fReq.name,
            language=detect_language(fReq.name),
            size_bytes=fReq.size,
            s3_key=s3_key,
            component_id=None,
            confirmed=False
        )
        db.add(project_file)
        await db.flush()
        
        upload_url = await generate_presigned_put_url(s3_key, fReq.content_type)
        
        response_data.append({
            "file_id": project_file.id,
            "upload_url": upload_url,
            "storage_key": s3_key
        })
        
    await db.commit()
    
    return {"data": response_data}

@router.post("/projects/{project_id}/files/confirm-batch")
async def confirm_upload_batch(project_id: str, req: ConfirmBatchReq, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    res = await db.execute(select(Project).where(Project.id == project_id))
    project = res.scalars().first()
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    for fid in req.file_ids:
        f_res = await db.execute(select(ProjectFile).where(ProjectFile.id == fid, ProjectFile.project_id == project_id))
        project_file = f_res.scalars().first()
        
        if project_file:
            exists = await object_exists(project_file.s3_key)
            if not exists:
                # Could mark invalid, or just delete row
                await db.delete(project_file)
            else:
                project_file.confirmed = True
                
    await db.commit()
    
    # Enqueue Celery task
    task = parse_project.delay(project_id)
    
    return {"data": {"task_id": task.id, "message": "Parsing started"}}

class GithubPreviewReq(BaseModel):
    repo_url: str
    branch: str

@router.post("/projects/{project_id}/github-import/preview")
async def preview_github_import(project_id: str, req: GithubPreviewReq, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    import httpx
    
    res = await db.execute(select(Project).where(Project.id == project_id))
    project = res.scalars().first()
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    github_token = current_user.github_access_token
    if not github_token:
         raise HTTPException(status_code=400, detail="No GitHub access token for user")
         
    # Parse repo_url: ex: https://github.com/Priyanka-Singh27/Ripple-CIA
    parts = req.repo_url.rstrip("/").split("/")
    if len(parts) < 2:
        raise HTTPException(status_code=400, detail="Invalid repo url")
    repo_owner = parts[-2]
    repo_name = parts[-1]
    
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/git/trees/{req.branch}?recursive=1"
    headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github.v3+json"}
    
    async with httpx.AsyncClient() as client:
        gh_res = await client.get(url, headers=headers)
        if gh_res.status_code != 200:
            raise HTTPException(status_code=gh_res.status_code, detail=f"GitHub API Error: {gh_res.text}")
            
    tree_data = gh_res.json().get("tree", [])
    
    allowed_exts = {".ts", ".tsx", ".js", ".jsx", ".py", ".go"}
    files = []
    
    for item in tree_data:
        if item.get("type") == "blob":
            path = item.get("path", "")
            import os
            _, ext = os.path.splitext(path)
            if ext in allowed_exts:
                files.append(path)
                
    return {"data": files}

class GithubConfirmReq(BaseModel):
    repo_url: str
    branch: str
    selected_paths: Optional[List[str]] = None

@router.post("/projects/{project_id}/github-import/confirm")
async def confirm_github_import(project_id: str, req: GithubConfirmReq, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    res = await db.execute(select(Project).where(Project.id == project_id))
    project = res.scalars().first()
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    from app.tasks.parsing import import_github_repo
    task = import_github_repo.delay(project_id, req.repo_url, req.branch, current_user.github_access_token)
    
    return {"data": {"task_id": task.id}}

@router.get("/projects/{project_id}/files")
async def list_project_files(project_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    res = await db.execute(select(Project).where(Project.id == project_id))
    project = res.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.owner_id != current_user.id:
        has_access = await db.execute(
            select(ComponentContributor)
            .join(Component)
            .where(
                Component.project_id == project_id,
                ComponentContributor.user_id == current_user.id
            )
        )
        if not has_access.scalars().first():
            raise HTTPException(status_code=403, detail="Not authorized")
            
    f_res = await db.execute(select(ProjectFile).where(ProjectFile.project_id == project_id))
    files = f_res.scalars().all()
    
    return {
        "data": [
            {
                "id": f.id,
                "path": f.path,
                "language": f.language,
                "size_bytes": f.size_bytes,
                "component_id": f.component_id
            } for f in files
        ]
    }

class AssignFilesReq(BaseModel):
    file_ids: List[str]
    component_id: str

@router.post("/projects/{project_id}/files/assign")
async def assign_files_to_component(project_id: str, req: AssignFilesReq, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    res = await db.execute(select(Project).where(Project.id == project_id))
    project = res.scalars().first()
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized or not owner")
        
    await db.execute(
        update(ProjectFile)
        .where(ProjectFile.id.in_(req.file_ids), ProjectFile.project_id == project_id)
        .values(component_id=req.component_id)
    )
    await db.commit()
    return {"message": "Files assigned successfully"}

@router.get("/files/{file_id}/content")
async def get_file_content(file_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    res = await db.execute(select(ProjectFile).where(ProjectFile.id == file_id))
    f = res.scalars().first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
        
    res_p = await db.execute(select(Project).where(Project.id == f.project_id))
    project = res_p.scalars().first()
    
    if project.owner_id != current_user.id:
        has_access = await db.execute(
            select(ComponentContributor)
            .join(Component)
            .where(
                Component.project_id == f.project_id,
                ComponentContributor.user_id == current_user.id
            )
        )
        if not has_access.scalars().first():
             raise HTTPException(status_code=403, detail="Not authorized")
             
    try:
        content_bytes = await download_bytes(f.s3_key)
        content_str = content_bytes.decode('utf8')
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not read file content from S3")
        
    return {"data": {"filename": f.path, "content": content_str, "language": f.language}}

class DraftUpdateReq(BaseModel):
    content: str
    
@router.post("/files/{file_id}/draft")
async def save_file_draft(file_id: str, req: DraftUpdateReq, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    res = await db.execute(select(ProjectFile).where(ProjectFile.id == file_id))
    f = res.scalars().first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
        
    if not f.component_id:
        raise HTTPException(status_code=400, detail="File is not assigned to a component")
        
    res_p = await db.execute(select(Project).where(Project.id == f.project_id))
    project = res_p.scalars().first()
    
    if project.owner_id != current_user.id:
        has_access = await db.execute(
            select(ComponentContributor)
            .where(
                ComponentContributor.component_id == f.component_id,
                ComponentContributor.user_id == current_user.id
            )
        )
        if not has_access.scalars().first():
            raise HTTPException(status_code=403, detail="Not authorized on this component")
            
    res_d = await db.execute(
        select(FileDraft)
        .where(
            FileDraft.file_id == file_id,
            FileDraft.author_id == current_user.id,
            FileDraft.is_active == True
        )
    )
    draft = res_d.scalars().first()
    
    from datetime import datetime, timezone
    if draft:
        draft.content = req.content
        draft.updated_at = datetime.now(timezone.utc)
    else:
        draft = FileDraft(
            file_id=file_id,
            author_id=current_user.id,
            content=req.content,
            is_active=True
        )
        db.add(draft)
        
    await db.commit()
    await db.refresh(draft)
    
    return {"data": {"id": draft.id, "file_id": draft.file_id, "is_active": draft.is_active, "updated_at": draft.updated_at.isoformat()}}

@router.get("/files/{file_id}/draft")
async def get_file_draft(file_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    res = await db.execute(select(ProjectFile).where(ProjectFile.id == file_id))
    f = res.scalars().first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
        
    res_p = await db.execute(select(Project).where(Project.id == f.project_id))
    project = res_p.scalars().first()
    
    if project.owner_id != current_user.id:
        has_access = await db.execute(
            select(ComponentContributor)
            .join(Component)
            .where(
                Component.project_id == f.project_id,
                ComponentContributor.user_id == current_user.id
            )
        )
        if not has_access.scalars().first():
             raise HTTPException(status_code=403, detail="Not authorized")
             
    res_d = await db.execute(
        select(FileDraft)
        .where(
            FileDraft.file_id == file_id,
            FileDraft.author_id == current_user.id,
            FileDraft.is_active == True
        )
    )
    draft = res_d.scalars().first()
    
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
        
    return {"data": {"id": draft.id, "content": draft.content, "updated_at": draft.updated_at.isoformat()}}

@router.get("/components/{cid}/files")
async def get_component_files(cid: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    res_comp = await db.execute(select(Component).where(Component.id == cid))
    comp = res_comp.scalars().first()
    if not comp:
        raise HTTPException(status_code=404, detail="Component not found")
        
    res_p = await db.execute(select(Project).where(Project.id == comp.project_id))
    project = res_p.scalars().first()
    
    if project.owner_id != current_user.id:
        has_access = await db.execute(
            select(ComponentContributor)
            .join(Component)
            .where(
                Component.project_id == project.id,
                ComponentContributor.user_id == current_user.id
            )
        )
        if not has_access.scalars().first():
             raise HTTPException(status_code=403, detail="Not authorized")
             
    f_res = await db.execute(select(ProjectFile).where(ProjectFile.component_id == cid))
    files = f_res.scalars().all()
    
    out = []
    for f in files:
        url = await generate_presigned_get_url(f.s3_key)
        out.append({
            "id": f.id,
            "path": f.path,
            "language": f.language,
            "size_bytes": f.size_bytes,
            "download_url": url
        })
        
    return {"data": out}

@router.get("/components/{cid}/dependencies")
async def get_component_dependencies(cid: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    res_comp = await db.execute(select(Component).where(Component.id == cid))
    comp = res_comp.scalars().first()
    if not comp:
        raise HTTPException(status_code=404, detail="Component not found")
        
    res_p = await db.execute(select(Project).where(Project.id == comp.project_id))
    project = res_p.scalars().first()
    
    if project.owner_id != current_user.id:
        has_access = await db.execute(
            select(ComponentContributor)
            .join(Component)
            .where(
                Component.project_id == project.id,
                ComponentContributor.user_id == current_user.id
            )
        )
        if not has_access.scalars().first():
             raise HTTPException(status_code=403, detail="Not authorized")
             
    from sqlalchemy.orm import selectinload
    
    deps_on_res = await db.execute(
        select(ComponentDependency)
        .options(selectinload(ComponentDependency.target_component))
        .where(ComponentDependency.source_component_id == cid)
    )
    depends_on = deps_on_res.scalars().all()
    
    deps_by_res = await db.execute(
        select(ComponentDependency)
        .options(selectinload(ComponentDependency.source_component))
        .where(ComponentDependency.target_component_id == cid)
    )
    depended_by = deps_by_res.scalars().all()
    
    return {"data": {
        "depends_on": [
            {
                "id": d.id, 
                "target_component_id": d.target_component_id,
                "target_component_name": d.target_component.name,
                "dependency_type": d.dependency_type
            } for d in depends_on
        ],
        "depended_by": [
            {
                "id": d.id, 
                "source_component_id": d.source_component_id,
                "source_component_name": d.source_component.name,
                "dependency_type": d.dependency_type
            } for d in depended_by
        ]
    }}
