from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routes import jobs

# Create database schemas directly during initialization if they do not exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI-Powered Transaction Processing Pipeline",
    version="1.0.0",
    description="Asynchronous cleaning, anomaly metrics filtering, and narrative reports generation via Gemini 1.5 Flash."
)

# Standard security CORS middleware configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount system endpoint routers
app.include_router(jobs.router)

@app.get("/")
def health_check():
    return {"status": "healthy", "service": "transaction-pipeline-api"}