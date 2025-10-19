from fastapi import FastAPI

app = FastAPI(title="Valuation Agent Backend", version="1.0.0")

@app.get("/healthz")
def health_check():
    return {"ok": True, "service": "backend"}

@app.get("/")
def root():
    return {"message": "Backend is running"}

