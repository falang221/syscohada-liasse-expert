from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.api.deps import get_current_user, db
from app.services.payment_service import initiate_payment, PRICE_PER_LIASSE
from app.services.audit_service import log_action
from pydantic import BaseModel

router = APIRouter()

class WebhookData(BaseModel):
    dossier_id: str
    status: str # SUCCESS or FAILED

@router.post("/initiate/{dossier_id}")
async def initiate_dossier_payment(dossier_id: str, request: Request, current_user = Depends(get_current_user)):
    # 1. Verify dossier exists and belongs to user's cabinet
    dossier = await db.dossier.find_first(
        where={
            "id": dossier_id,
            "client": {
                "cabinetId": current_user.cabinetId
            }
        },
        include={"client": True}
    )
    
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier introuvable")
    
    if dossier.isPaid:
        return {"detail": "Dossier déjà payé", "payment_url": None}

    # 2. Create Payment record in PENDING
    payment = await db.payment.create(
        data={
            "amount": float(PRICE_PER_LIASSE),
            "currency": "XOF",
            "status": "PENDING",
            "dossierId": dossier_id,
            "userId": current_user.id
        }
    )
    
    # 3. Call service to get payment URL
    item_name = f"Liasse Fiscale {dossier.year} - {dossier.client.name}"
    payment_url = await initiate_payment(dossier_id, item_name)
    
    await log_action(
        db,
        action="INITIATE_PAYMENT",
        entity="Payment",
        entity_id=payment.id,
        user_id=current_user.id,
        new_value={"dossier_id": dossier_id, "amount": PRICE_PER_LIASSE},
        ip_address=request.client.host
    )
    
    return {"payment_url": payment_url}

@router.post("/webhook")
async def payment_webhook(data: WebhookData, request: Request):
    # In a real app, we would verify the signature/source of the webhook
    
    if data.status == "SUCCESS":
        # 1. Find the pending payment for this dossier
        payment = await db.payment.find_first(
            where={
                "dossierId": data.dossier_id,
                "status": "PENDING"
            },
            order={"createdAt": "desc"}
        )
        
        if payment:
            # 2. Update Payment status
            await db.payment.update(
                where={"id": payment.id},
                data={"status": "SUCCESS"}
            )
            
            # 3. Update Dossier isPaid
            await db.dossier.update(
                where={"id": data.dossier_id},
                data={"isPaid": True}
            )
            
            await log_action(
                db,
                action="WEBHOOK_SUCCESS",
                entity="Payment",
                entity_id=payment.id,
                user_id=payment.userId,
                new_value={"dossier_id": data.dossier_id, "status": "SUCCESS"},
                ip_address=request.client.host
            )
        else:
            # Maybe it was already updated or dossier_id is wrong
            pass
    
    return {"status": "ok"}
