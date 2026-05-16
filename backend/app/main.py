from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import pandas as pd
import io

from app.services.excel_parser import parse_balance_df
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
        
        # Parse the balance (currently a mock/basic implementation)
        parsed_data = parse_balance_df(df)
        
        # Prepare data for PDF generation
        pdf_data = {
            "cabinet_name": "Cabinet d'Expertise Postefinances",
            "dossier_name": "Client Démo",
            "exercice": "2026",
            "title": "Bilan SYSCOHADA (Aperçu)",
            "table_rows": []
        }
        
        # Simple mapping for demo purposes
        for row in parsed_data:
            # Assumes columns 'compte', 'intitulé', 'débit', 'crédit' exist, falling back safely
            pdf_data["table_rows"].append({
                "code": str(row.get("compte", "")),
                "label": str(row.get("intitulé", row.get("compte", "Inconnu"))),
                "brut": row.get("débit", 0) or row.get("solde_debit", 0),
                "amort": 0,
                "net_n": row.get("débit", 0) or row.get("solde_debit", 0),
                "net_n_1": 0,
                "is_total": False
            })
            
        pdf_bytes = generate_liasse_pdf(pdf_data)
        
        return Response(content=pdf_bytes, media_type="application/pdf", headers={
            "Content-Disposition": f"attachment; filename=Liasse_{file.filename}.pdf"
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
