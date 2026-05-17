from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.security import OAuth2PasswordRequestForm
import pandas as pd
import io
import json
from typing import Optional

from app.services.excel_parser import parse_balance_df
from app.services.financial_engine import compute_financial_statements
from app.services.pdf_service import generate_liasse_pdf
from app.core.security import verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta
from prisma import Prisma
from app.api.deps import get_current_user, db
from app.api import clients, users

app = FastAPI(title="SYSCOHADA Liasse-Expert API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(clients.router, prefix="/api/clients", tags=["Clients"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])

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

@app.post("/api/analyze-balances")
async def analyze_balances(
    file_n: UploadFile = File(...),
    file_n_1: Optional[UploadFile] = File(None),
    current_user = Depends(get_current_user)
):
    """Parses balances and returns the raw financial statements (JSON) for the wizard."""
    if not file_n.filename.endswith(('.xls', '.xlsx')):
        raise HTTPException(status_code=400, detail="Invalid file type for Balance N.")
    
    try:
        contents_n = await file_n.read()
        df_n = pd.read_excel(io.BytesIO(contents_n), engine='openpyxl' if file_n.filename.endswith('.xlsx') else None)
        parsed_data_n = parse_balance_df(df_n)
        
        parsed_data_n_1 = None
        if file_n_1 and file_n_1.filename.strip():
            contents_n_1 = await file_n_1.read()
            df_n_1 = pd.read_excel(io.BytesIO(contents_n_1), engine='openpyxl' if file_n_1.filename.endswith('.xlsx') else None)
            parsed_data_n_1 = parse_balance_df(df_n_1)

        statements = compute_financial_statements(parsed_data_n, parsed_data_n_1)
        return statements
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-liasse")
async def generate_liasse(
    file_n: UploadFile = File(...), 
    file_n_1: Optional[UploadFile] = File(None),
    client_id: Optional[str] = Form(None),
    exercice: Optional[str] = Form("2024"),
    adjustments: Optional[str] = Form(None), # JSON string
    current_user = Depends(get_current_user)
):
    if not file_n.filename.endswith(('.xls', '.xlsx')):
        raise HTTPException(status_code=400, detail="Invalid file type for Balance N. Please upload an Excel file.")
    
    try:
        # Process N
        contents_n = await file_n.read()
        df_n = pd.read_excel(io.BytesIO(contents_n), engine='openpyxl' if file_n.filename.endswith('.xlsx') else None)
        parsed_data_n = parse_balance_df(df_n)
        
        if not parsed_data_n:
             raise HTTPException(status_code=400, detail="No valid data found in Balance N.")

        # Process N-1 if provided
        parsed_data_n_1 = None
        if file_n_1 and file_n_1.filename.strip():
            try:
                contents_n_1 = await file_n_1.read()
                df_n_1 = pd.read_excel(io.BytesIO(contents_n_1), engine='openpyxl' if file_n_1.filename.endswith('.xlsx') else None)
                parsed_data_n_1 = parse_balance_df(df_n_1)
            except Exception as e_n1:
                print(f"WARNING: Failed to parse N-1 file: {str(e_n1)}")

        statements = compute_financial_statements(parsed_data_n, parsed_data_n_1)
        
        # Apply adjustments if provided
        if adjustments:
            adj_data = json.loads(adjustments)
            # Adjust TAFIRE flows
            if "tafire" in statements:
                for key, val in adj_data.items():
                    if key in statements["tafire"]:
                        statements["tafire"][key] += float(val)
                    elif key == "investissement_adj":
                         statements["tafire"]["investissement"] += float(val)
                    elif key == "financement_adj":
                         statements["tafire"]["financement"] += float(val)
                
                # Re-calculate variation and coherence
                statements["tafire"]["variation_tresorerie"] = (
                    statements["tafire"]["activite"] + 
                    statements["tafire"]["investissement"] + 
                    statements["tafire"]["financement"]
                )
                # Coherence check (simplified)
                # ... already handled in engine, but we could update it here too

        # Fetch client info if available
        dossier_name = file_n.filename.replace(".xlsx", "").replace(".xls", "")
        client_info = {}
        if client_id:
            client = await db.client.find_unique(where={"id": client_id})
            if client:
                dossier_name = client.name
                client_info = {
                    "ninea": client.ninea,
                    "rccm": client.rccm,
                    "adresse": client.adresse
                }

        pdf_data = {
            "cabinet_name": "Cabinet d'Expertise Postefinances",
            "dossier_name": dossier_name,
            "client_info": client_info,
            "exercice": exercice,
            "title": "Liasse Fiscale SYSCOHADA (Expert)",
            "statements": statements
        }
            
        pdf_bytes = generate_liasse_pdf(pdf_data)
        
        return Response(content=pdf_bytes, media_type="application/pdf", headers={
            "Content-Disposition": f"attachment; filename=Liasse_{dossier_name}_{exercice}.pdf"
        })
        
    except Exception as e:
        print(f"ERROR during generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")

