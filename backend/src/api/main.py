from fastapi import FastAPI

app = FastAPI(
    title="Financial Assistant API",
    description="API for Financial Assistant with OCR and Expense Management",
    version="0.1.0"
)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}