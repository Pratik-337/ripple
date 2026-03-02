import asyncio
from datetime import datetime, timedelta, timezone
from app.worker import celery_app
from app.core.database import AsyncSessionLocal
from sqlalchemy import select
from app.models.change import ChangeRequest, ChangeImpact, Notification
from app.core.redis import publish
import json

def _run_async(coro):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)

async def _auto_confirm_stale_impacts():
    async with AsyncSessionLocal() as db:
        time_limit = datetime.now(timezone.utc) - timedelta(hours=24)
        
        # Impacts that are unacknowledged and where parent CR is older than 24h
        stmt = (
            select(ChangeImpact, ChangeRequest)
            .join(ChangeRequest, ChangeImpact.change_request_id == ChangeRequest.id)
            .where(
                ChangeImpact.acknowledged == False,
                ChangeImpact.dismissed == False,
                ChangeRequest.created_at < time_limit
            )
        )
        res = await db.execute(stmt)
        rows = res.all()
        
        change_requests_to_check = set()
        
        for imp, cr in rows:
            print(f"Auto-confirming impact {imp.id} for CR {cr.id}")
            imp.acknowledged = True
            imp.acknowledged_at = datetime.now(timezone.utc)
            
            # Notification
            n = Notification(
                user_id=imp.contributor_id,
                type="change",
                title="Impact Auto-Confirmed",
                body=f"Your acknowledgement for change '{cr.title}' was auto-confirmed after 24h.",
                link=f"/changes/{cr.id}"
            )
            db.add(n)
            
            # Publish WS event
            await publish(
                f"ws:user:{imp.contributor_id}", json.dumps({
                    "event": "change:auto_confirmed",
                    "data": {"change_request_id": cr.id}
                })
            )
            
            change_requests_to_check.add(cr)
            
        await db.flush()
            
        # Check if all impacts for any of these changes are now acknowledged
        for cr in change_requests_to_check:
            all_imp_res = await db.execute(select(ChangeImpact).where(ChangeImpact.change_request_id == cr.id))
            all_impacts = all_imp_res.scalars().all()
            
            all_ack = True
            for i in all_impacts:
                if not i.acknowledged and not i.dismissed:
                    all_ack = False
                    break
                    
            if all_ack:
                cr.status = "pending_review"
                
        await db.commit()

@celery_app.task
def auto_confirm_stale_impacts():
    _run_async(_auto_confirm_stale_impacts())
