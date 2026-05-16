# SYSCOHADA Liasse-Expert Implementation Plan (MVP)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a functional MVP that generates a basic SYSCOHADA Balance and Income Statement (Compte de Résultat) from an Excel upload, with a validation dashboard and PDF export.

**Architecture:** Backend-heavy financial logic in FastAPI, interactive validation frontend in Next.js, and automated PDF generation using WeasyPrint.

**Tech Stack:** FastAPI, Next.js, PostgreSQL, Prisma, Pandas, WeasyPrint.

---

## Phase 1: Project Setup & Core Models

### Task 1: Backend Scaffolding
**Files:**
- Create: `backend/app/main.py`
- Create: `backend/app/core/config.py`
- Create: `backend/requirements.txt`

- [ ] **Step 1: Create requirements.txt**
```text
fastapi
uvicorn
pandas
openpyxl
pydantic-settings
python-multipart
sqlalchemy
psycopg2-binary
weasyprint
```

- [ ] **Step 2: Create basic FastAPI app**
```python
from fastapi import FastAPI
app = FastAPI(title="SYSCOHADA Liasse-Expert API")

@app.get("/")
def read_root():
    return {"status": "ok"}
```

- [ ] **Step 3: Commit**
```bash
git add backend/
git commit -m "chore: initial backend scaffold"
```

### Task 2: Database Schema (Prisma)
**Files:**
- Create: `backend/prisma/schema.prisma`

- [ ] **Step 1: Define models for Cabinet, Dossier, and AccountMapping**
```prisma
model Cabinet {
  id    String   @id @default(cuid())
  name  String
  users User[]
  dossiers Dossier[]
}

model User {
  id        String   @id @default(cuid())
  username  String   @unique
  role      String   @default("COLLABORATOR") // ADMIN, COLLABORATOR
  cabinetId String
  cabinet   Cabinet  @relation(fields: [cabinetId], references: [id])
}

model Dossier {
  id        String   @id @default(cuid())
  name      String
  year      Int
  cabinetId String
  cabinet   Cabinet  @relation(fields: [cabinetId], references: [id])
  mappings  AccountMapping[]
}

model AccountMapping {
  id        String   @id @default(cuid())
  account   String   // Root account (e.g., "601")
  rubrique  String   // SYSCOHADA Rubrique code
  dossierId String
  dossier   Dossier  @relation(fields: [dossierId], references: [id])
}
```

- [ ] **Step 2: Commit**
```bash
git add backend/prisma/schema.prisma
git commit -m "feat: add initial database schema"
```

---

## Phase 2: Financial Engine (The "Brain")

### Task 3: Excel Parsing Service
**Files:**
- Create: `backend/app/services/excel_parser.py`
- Test: `backend/tests/test_excel_parser.py`

- [ ] **Step 1: Write test for Excel parsing**
```python
def test_parse_balance():
    # Mock excel data
    data = {"compte": ["601", "701"], "debit": [100, 0], "credit": [0, 150]}
    df = pd.DataFrame(data)
    # Expected: dict or list of objects
    result = parse_balance_df(df)
    assert len(result) == 2
```

- [ ] **Step 2: Implement parse_balance_df**
```python
import pandas as pd

def parse_balance_df(df: pd.DataFrame):
    return df.to_dict(orient="records")
```

- [ ] **Step 3: Commit**
```bash
git add backend/app/services/excel_parser.py
git commit -m "feat: implement basic excel parser"
```

---

## Phase 3: Frontend Dashboard

### Task 4: Frontend Scaffolding (Next.js)
**Files:**
- Create: `frontend/package.json`
- Create: `frontend/src/app/page.tsx`

- [ ] **Step 1: Setup basic Next.js with Tailwind**
- [ ] **Step 2: Create Landing Page with Upload zone**
- [ ] **Step 3: Commit**

---

## Phase 4: PDF Generation

### Task 5: PDF Export Service
**Files:**
- Create: `backend/app/services/pdf_service.py`
- Create: `backend/app/templates/liasse_template.html`

- [ ] **Step 1: Create HTML template for Bilan**
- [ ] **Step 2: Implement WeasyPrint conversion**
- [ ] **Step 3: Commit**
