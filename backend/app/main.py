from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.security import OAuth2PasswordRequestForm
import pandas as pd
import io

from app.services.excel_parser import parse_balance_df
from app.services.financial_engine import compute_financial_statements
from app.services.pdf_service import generate_liasse_pdf
from app.core.security import verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta
from prisma import Prisma
from app.api.deps import get_current_user, db

app = FastAPI(title="SYSCOHADA Liasse-Expert API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    if not db.is_connected():
        await db.connect()

@app.on_event("shutdown")
async def shutdown():
    if db.is_connected():
        await db.disconnect()

@app.post("/api/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db.user.find_unique(where={"username": form_data.username})
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.username, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}

@app.get("/api/users/me")
async def read_users_me(current_user = Depends(get_current_user)):
    return {"username": current_user.username, "role": current_user.role}

@app.post("/api/generate-liasse")
async def generate_liasse(file: UploadFile = File(...), current_user = Depends(get_current_user)):
    if not file.filename.endswith(('.xls', '.xlsx')):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an Excel file.")
    
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        parsed_data = parse_balance_df(df)
        statements = compute_financial_statements(parsed_data)
        
        pdf_data = {
            "cabinet_name": "Cabinet d'Expertise Postefinances", # Could be fetched via current_user.cabinet
            "dossier_name": "Client Démo",
            "exercice": "2026",
            "title": "Liasse Fiscale SYSCOHADA (MVP)",
            "statements": statements
        }
            
        pdf_bytes = generate_liasse_pdf(pdf_data)
        
        return Response(content=pdf_bytes, media_type="application/pdf", headers={
            "Content-Disposition": f"attachment; filename=Liasse_{file.filename}.pdf"
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
