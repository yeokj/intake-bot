from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI(
    title="TIQC Client Intake API",
    version="0.1.0",
    description="API backend for TIQC AI Client Intake & Project Scoping Bot"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HealthCheck(BaseModel):
    status: str = "OK"

@app.get("/health", status_code=status.HTTP_200_OK, response_model=HealthCheck)
async def liveness_check():
    return {"status": "OK"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)