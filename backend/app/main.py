from fastapi import FastAPI
app = FastAPI(title="SYSCOHADA Liasse-Expert API")

@app.get("/")
def read_root():
    return {"status": "ok"}
