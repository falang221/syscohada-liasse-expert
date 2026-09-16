from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List, Optional
from app.api.deps import get_current_user, db
from pydantic import BaseModel
from app.services.audit_service import log_action
from datetime import datetime

router = APIRouter()

class ClientCreate(BaseModel):
    name: str
    ninea: str
    rccm: Optional[str] = None
    adresse: Optional[str] = None
    capitalSocial: Optional[float] = None

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    ninea: Optional[str] = None
    rccm: Optional[str] = None
    adresse: Optional[str] = None
    capitalSocial: Optional[float] = None

@router.get("/", response_model=List[dict])
async def list_clients(current_user = Depends(get_current_user)):
    clients = await db.client.find_many(
        where={
            "cabinetId": current_user.cabinetId,
            "deletedAt": None
        },
        order={"name": "asc"}
    )
    return [client.dict() for client in clients]

@router.post("/", response_model=dict)
async def create_client(data: ClientCreate, request: Request, current_user = Depends(get_current_user)):
    # Check if ninea already exists
    existing = await db.client.find_unique(where={"ninea": data.ninea})
    if existing:
        if existing.deletedAt:
            # Restore soft deleted client? Or just error? Let's just error for simplicity or restore.
            # For now, let's just raise error.
            raise HTTPException(status_code=400, detail="Client with this NINEA already exists (even if deleted)")
        raise HTTPException(status_code=400, detail="Client with this NINEA already exists")

    client = await db.client.create(
        data={
            **data.dict(),
            "cabinetId": current_user.cabinetId
        }
    )
    
    await log_action(
        db, 
        action="CREATE", 
        entity="Client", 
        entity_id=client.id, 
        user_id=current_user.id, 
        new_value=data.dict(),
        ip_address=request.client.host
    )
    
    return client.dict()

@router.get("/{id}", response_model=dict)
async def get_client(id: str, current_user = Depends(get_current_user)):
    client = await db.client.find_first(
        where={
            "id": id,
            "cabinetId": current_user.cabinetId,
            "deletedAt": None
        }
    )
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client.dict()

@router.patch("/{id}", response_model=dict)
async def update_client(id: str, data: ClientUpdate, request: Request, current_user = Depends(get_current_user)):
    client = await db.client.find_first(
        where={
            "id": id,
            "cabinetId": current_user.cabinetId,
            "deletedAt": None
        }
    )
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    old_data = {k: getattr(client, k) for k in data.dict(exclude_unset=True).keys()}
    
    updated_client = await db.client.update(
        where={"id": id},
        data=data.dict(exclude_unset=True)
    )
    
    await log_action(
        db, 
        action="UPDATE", 
        entity="Client", 
        entity_id=id, 
        user_id=current_user.id, 
        old_value=old_data,
        new_value=data.dict(exclude_unset=True),
        ip_address=request.client.host
    )
    
    return updated_client.dict()

@router.delete("/{id}")
async def delete_client(id: str, request: Request, current_user = Depends(get_current_user)):
    client = await db.client.find_first(
        where={
            "id": id,
            "cabinetId": current_user.cabinetId,
            "deletedAt": None
        }
    )
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    await db.client.update(
        where={"id": id},
        data={"deletedAt": datetime.now()}
    )
    
    await log_action(
        db, 
        action="DELETE", 
        entity="Client", 
        entity_id=id, 
        user_id=current_user.id, 
        ip_address=request.client.host
    )
    
    return {"detail": "Client soft-deleted successfully"}
