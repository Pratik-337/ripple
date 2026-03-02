from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, or_
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone
import json

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.component import Component, ComponentContributor
from app.models.change import Notification, Invite
from app.core.redis import publish

router = APIRouter(tags=["users_and_notifications"])

@router.get("/notifications")
async def list_notifications(
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    q = select(Notification).where(Notification.user_id == current_user.id).order_by(Notification.created_at.desc())
    if unread_only:
        q = q.where(Notification.is_read == False)
        
    count_q = select(func.count()).select_from(q.subquery())
    total_res = await db.execute(count_q)
    total = total_res.scalar_one()

    q = q.offset((page - 1) * limit).limit(limit)
    res = await db.execute(q)
    notifs = res.scalars().all()
    
    return {
        "data": [
            {
                "id": n.id,
                "type": n.type,
                "title": n.title,
                "body": n.body,
                "link": n.link,
                "meta_data": n.meta_data,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat()
            } for n in notifs
        ],
        "meta": {
            "total_unread": total if unread_only else None, # approximate
            "page": page,
            "has_next": (page * limit) < total
        }
    }

class MarkReadReq(BaseModel):
    ids: Optional[List[str]] = None
    all: Optional[bool] = False

@router.post("/notifications/mark-read")
async def mark_notifications_read(req: MarkReadReq, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if req.all:
        res = await db.execute(
            update(Notification)
            .where(Notification.user_id == current_user.id, Notification.is_read == False)
            .values(is_read=True)
        )
        updated_count = res.rowcount
    elif req.ids:
        res = await db.execute(
            update(Notification)
            .where(Notification.id.in_(req.ids), Notification.user_id == current_user.id, Notification.is_read == False)
            .values(is_read=True)
        )
        updated_count = res.rowcount
    else:
        updated_count = 0
        
    await db.commit()
    return {"data": {"updated_count": updated_count}}

class InviteReq(BaseModel):
    email: EmailStr
    component_id: Optional[str] = None
    role: str = "contributor"

@router.post("/projects/{project_id}/invites")
async def create_invite(project_id: str, req: InviteReq, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    res = await db.execute(select(Project).where(Project.id == project_id))
    proj = res.scalars().first()
    if not proj or proj.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only project owner can invite")
        
    u_res = await db.execute(select(User).where(User.email == req.email))
    target_user = u_res.scalars().first()
    
    invite = Invite(
        project_id=project_id,
        component_id=req.component_id,
        invited_by=current_user.id,
        invited_email=req.email,
        role=req.role,
        status="pending"
    )
    db.add(invite)
    await db.flush()
    
    if target_user:
        n = Notification(
            user_id=target_user.id,
            type="invite",
            title="New Project Invite",
            body=f"You have been invited to collaborate on project '{proj.name}'",
            link="/invites",
            meta_data={"invite_id": invite.id}
        )
        db.add(n)
        await db.commit()
        await publish(
            f"ws:user:{target_user.id}", json.dumps({
                "event": "invite:received",
                "data": {"invite_id": invite.id}
            })
        )
    else:
        await db.commit()
        
    return {"data": {
        "id": invite.id,
        "invited_email": invite.invited_email,
        "status": invite.status
    }}

@router.get("/invites/pending")
async def get_pending_invites(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    from sqlalchemy.orm import selectinload
    res = await db.execute(
        select(Invite)
        .options(
            selectinload(Invite.project),
            selectinload(Invite.inviter),
            selectinload(Invite.component)
        )
        .where(
            Invite.invited_email == current_user.email,
            Invite.status == "pending"
        )
    )
    invites = res.scalars().all()
    
    return {"data": [
        {
            "id": i.id,
            "project_name": i.project.name,
            "component_name": i.component.name if i.component else None,
            "invited_by": i.inviter.display_name,
            "role": i.role,
            "created_at": i.created_at.isoformat()
        } for i in invites
    ]}

@router.post("/invites/{invite_id}/accept")
async def accept_invite(invite_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    res = await db.execute(select(Invite).where(Invite.id == invite_id))
    invite = res.scalars().first()
    if not invite or invite.status != "pending" or invite.invited_email != current_user.email:
        raise HTTPException(status_code=404, detail="Invite not found or already actioned")
        
    invite.status = "accepted"
    
    if invite.component_id:
        cc = ComponentContributor(
            component_id=invite.component_id,
            user_id=current_user.id,
            role=invite.role,
            granted_at=datetime.now(timezone.utc),
            granted_by=invite.invited_by
        )
        db.add(cc)
        
    await db.commit()
    
    return {"data": {
        "project_id": invite.project_id,
        "component_id": invite.component_id,
        "role": invite.role
    }}

@router.post("/invites/{invite_id}/decline")
async def decline_invite(invite_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    res = await db.execute(select(Invite).where(Invite.id == invite_id))
    invite = res.scalars().first()
    if not invite or invite.status != "pending" or invite.invited_email != current_user.email:
        raise HTTPException(status_code=404, detail="Invite not found or already actioned")
        
    invite.status = "declined"
    await db.commit()
    
    return {"data": {"status": "declined"}}
