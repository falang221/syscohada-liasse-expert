from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import pandas as pd
import io

from app.services.excel_parser import parse_balance_df
from app.services.financial_engine import compute_financial_statements
from app.services.pdf_service import generate_liasse_pdf

app = FastAPI(title="SYSCOHADA Liasse-Expert API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ok"}

@app.post("/api/generate-liasse")
async def generate_liasse(file: UploadFile = File(...)):
    if not file.filename.endswith(('.xls', '.xlsx')):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an Excel file.")
    
    try:
        contents = await file.read()
        # Read the Excel file into a pandas DataFrame
        df = pd.read_excel(io.BytesIO(contents))
        
        # Parse the balance
        parsed_data = parse_balance_df(df)
        
        # Use the financial engine to aggregate data
        statements = compute_financial_statements(parsed_data)
        
        # Prepare data for PDF generation
        pdf_data = {
            "cabinet_name": "Cabinet d'Expertise Postefinances",
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
