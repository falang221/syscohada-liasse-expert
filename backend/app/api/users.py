from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime
from app.api.deps import get_current_user, check_admin, db
from app.core.security import get_password_hash
from pydantic import BaseModel

router = APIRouter()

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "COLLABORATOR"

class UserOut(BaseModel):
    id: str
    username: str
    role: str
    createdAt: datetime

@router.get("/", response_model=List[UserOut])
async def list_team_members(current_user = Depends(check_admin)):
    return await db.user.find_many(
        where={"cabinetId": current_user.cabinetId, "deletedAt": None},
        order={"createdAt": "desc"}
    )

@router.post("/", response_model=UserOut)
async def add_team_member(data: UserCreate, current_user = Depends(check_admin)):
    existing = await db.user.find_unique(where={"username": data.username})
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nom d'utilisateur déjà utilisé.")
    
    return await db.user.create(
        data={
            "username": data.username,
            "hashed_password": get_password_hash(data.password),
            "role": data.role,
            "cabinetId": current_user.cabinetId
        }
    )

@router.delete("/{user_id}", response_model=dict)
async def delete_team_member(user_id: str, current_user = Depends(check_admin)):
    # Prevent self-deletion for MVP
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vous ne pouvez pas vous supprimer vous-même.")
        
    user = await db.user.find_first(where={"id": user_id, "cabinetId": current_user.cabinetId})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé.")
        
    await db.user.update(
        where={"id": user_id},
        data={"deletedAt": datetime.utcnow()}
    )
    return {"message": "Utilisateur supprimé avec succès."}
