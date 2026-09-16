from prisma import Prisma
from datetime import datetime
import json

async def log_action(db, action: str, entity: str, entity_id: str = None, user_id: str = None, old_value: dict = None, new_value: dict = None, ip_address: str = None):
    await db.auditlog.create(
        data={
            "action": action,
            "entity": entity,
            "entityId": entity_id,
            "userId": user_id,
            "oldValue": json.dumps(old_value) if old_value else None,
            "newValue": json.dumps(new_value) if new_value else None,
            "ipAddress": ip_address
        }
    )
