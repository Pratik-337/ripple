from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.component import Component, ComponentContributor, ProjectFile
from app.models.change import Notification
from app.core.redis import publish
import json

from pydantic import BaseModel

router = APIRouter(prefix="/projects/{project_id}/components", tags=["components"])

class ComponentCreate(BaseModel):
    name: str

class ComponentUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None

class ContributorAdd(BaseModel):
    user_id: str
    role: str

async def verify_project_access(project_id: str, current_user: User, db: AsyncSession, require_owner: bool = False):
    res = await db.execute(select(Project).where(Project.id == project_id))
    project = res.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if require_owner:
        if project.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Only project owner can perform this action")
        return project

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
            raise HTTPException(status_code=403, detail="Not authorized to access project components")
            
    return project

@router.post("")
async def create_component(project_id: str, req: ComponentCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    await verify_project_access(project_id, current_user, db, require_owner=True)
    
    new_comp = Component(
        project_id=project_id,
        name=req.name,
        status="stable"
    )
    db.add(new_comp)
    await db.commit()
    await db.refresh(new_comp)

    return {
        "data": {
            "id": new_comp.id,
            "name": new_comp.name,
            "status": new_comp.status,
            "color": new_comp.color,
            "created_at": new_comp.created_at.isoformat()
        }
    }

@router.get("")
async def list_components(project_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    await verify_project_access(project_id, current_user, db, require_owner=False)

    comp_res = await db.execute(
        select(Component)
        .options(
            selectinload(Component.contributors).selectinload(ComponentContributor.user),
            selectinload(Component.files)
        )
        .where(Component.project_id == project_id)
    )
    components = comp_res.scalars().all()

    return {
        "data": [
            {
                "id": c.id,
                "name": c.name,
                "status": c.status,
                "color": c.color,
                "created_at": c.created_at.isoformat(),
                "file_count": len(c.files),
                "contributors": [
                    {
                        "user_id": cb.user.id,
                        "display_name": cb.user.display_name,
                        "email": cb.user.email,
                        "avatar_url": cb.user.avatar_url,
                        "role": cb.role
                    } for cb in c.contributors
                ]
            } for c in components
        ]
    }

@router.patch("/{component_id}")
async def update_component(project_id: str, component_id: str, req: ComponentUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    await verify_project_access(project_id, current_user, db, require_owner=True)

    res = await db.execute(select(Component).where(Component.id == component_id, Component.project_id == project_id))
    comp = res.scalars().first()
    if not comp:
        raise HTTPException(status_code=404, detail="Component not found")

    if req.name is not None:
        comp.name = req.name
    if req.status is not None:
        comp.status = req.status

    await db.commit()
    await db.refresh(comp)

    return {
        "data": {
            "id": comp.id,
            "name": comp.name,
            "status": comp.status,
            "color": comp.color
        }
    }

@router.delete("/{component_id}")
async def delete_component(project_id: str, component_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    await verify_project_access(project_id, current_user, db, require_owner=True)

    res = await db.execute(select(Component).where(Component.id == component_id, Component.project_id == project_id))
    comp = res.scalars().first()
    if not comp:
        raise HTTPException(status_code=404, detail="Component not found")

    # Unassign files
    await db.execute(
        update(ProjectFile)
        .where(ProjectFile.component_id == component_id)
        .values(component_id=None)
    )

    await db.delete(comp)
    await db.commit()

    return {"message": "Component deleted"}

@router.post("/{component_id}/contributors")
async def add_contributor(project_id: str, component_id: str, req: ContributorAdd, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = await verify_project_access(project_id, current_user, db, require_owner=True)

    res_comp = await db.execute(select(Component).where(Component.id == component_id, Component.project_id == project_id))
    comp = res_comp.scalars().first()
    if not comp:
        raise HTTPException(status_code=404, detail="Component not found")

    res_user = await db.execute(select(User).where(User.id == req.user_id))
    target_user = res_user.scalars().first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    exist_res = await db.execute(
        select(ComponentContributor)
        .where(
            ComponentContributor.component_id == component_id,
            ComponentContributor.user_id == req.user_id
        )
    )
    if exist_res.scalars().first():
        raise HTTPException(status_code=409, detail="User is already a contributor to this component")

    contrib = ComponentContributor(
        component_id=component_id,
        user_id=req.user_id,
        role=req.role,
        granted_by=current_user.id
    )
    db.add(contrib)

    notif = Notification(
        user_id=req.user_id,
        type="invite",
        title="Added to Component",
        body=f"You have been added to the component '{comp.name}' in project '{project.name}' as a {req.role}.",
        link=f"/projects/{project.id}",
        meta_data={"project_id": project.id, "component_id": component_id}
    )
    db.add(notif)
    
    await db.commit()
    await db.refresh(notif)

    await publish(
        f"ws:user:{req.user_id}",
        json.dumps({
            "event": "notification:new",
            "data": {
                "id": notif.id,
                "title": notif.title,
                "body": notif.body,
                "link": notif.link,
                "created_at": notif.created_at.isoformat()
            }
        })
    )

    return {"message": "Contributor added successfully"}

@router.delete("/{component_id}/contributors/{user_id}")
async def remove_contributor(project_id: str, component_id: str, user_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    await verify_project_access(project_id, current_user, db, require_owner=True)

    res = await db.execute(
        select(ComponentContributor)
        .where(
            ComponentContributor.component_id == component_id,
            ComponentContributor.user_id == user_id
        )
    )
    contrib = res.scalars().first()
    if not contrib:
        raise HTTPException(status_code=404, detail="Contributor not found")

    await db.delete(contrib)
    await db.commit()

    return {"message": "Contributor removed successfully"}
