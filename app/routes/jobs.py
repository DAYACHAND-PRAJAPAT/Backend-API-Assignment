import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.job import Job
from app.models.transaction import Transaction
from app.models.summary import JobSummary
from app.tasks import process_csv_pipeline

router = APIRouter(prefix="/jobs", tags=["Jobs Pipeline"])

@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
def upload_transactions_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Accepts CSV file upload, triggers background task, and returns job_id immediately."""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only valid CSV files are allowed.")
        
    try:
        contents = file.file.read()
        job_id = str(uuid.uuid4())
        
        # Instantiate base job model state
        new_job = Job(id=job_id, filename=file.filename, status="pending")
        db.add(new_job)
        db.commit()
        
        # Trigger Celery Worker background pipeline asynchronously
        process_csv_pipeline.delay(job_id, contents)
        
        return {"job_id": job_id, "status": "pending", "message": "Pipeline execution started successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate pipeline: {str(e)}")

@router.get("/{job_id}/status")
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Returns the high-level operational tracking parameters for a given job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Requested job execution identifier not found.")
        
    response = {
        "job_id": job.id,
        "filename": job.filename,
        "status": job.status,
        "created_at": job.created_at,
        "completed_at": job.completed_at,
        "error_message": job.error_message
    }
    
    # If completed, append lightweight high-level statistics parameters natively
    if job.status == "completed":
        summary = db.query(JobSummary).filter(JobSummary.job_id == job_id).first()
        if summary:
            response["summary_stats"] = {
                "raw_rows": job.row_count_raw,
                "clean_rows": job.row_count_clean,
                "anomalies_detected": summary.anomaly_count,
                "risk_assessment": summary.risk_level
            }
    return response

@router.get("/{job_id}/results")
def get_job_results(job_id: str, db: Session = Depends(get_db)):
    """Returns full comprehensive insights structure including cleaned rows and narratives."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job execution data records not found.")
    if job.status != "completed":
        raise HTTPException(status_code=400, detail=f"Results unavailable. Current job status: {job.status}")
        
    transactions = db.query(Transaction).filter(Transaction.job_id == job_id).all()
    summary = db.query(JobSummary).filter(JobSummary.job_id == job_id).first()
    
    return {
        "job_metadata": {
            "job_id": job.id,
            "filename": job.filename,
            "raw_row_count": job.row_count_raw,
            "cleaned_row_count": job.row_count_clean
        },
        "narrative_report": {
            "total_spend_inr": summary.total_spend_inr if summary else 0,
            "total_spend_usd": summary.total_spend_usd if summary else 0,
            "top_merchants": summary.top_merchants if summary else [],
            "anomaly_count": summary.anomaly_count if summary else 0,
            "narrative": summary.narrative if summary else "",
            "risk_level": summary.risk_level if summary else "low"
        },
        "flagged_anomalies": [t for t in transactions if t.is_anomaly],
        "cleaned_transactions": transactions
    }

@router.get("")
def list_all_jobs(status: str = Query(None), db: Session = Depends(get_db)):
    """Lists history summaries of all pipeline run tasks execution lists."""
    query = db.query(Job)
    if status:
        query = query.filter(Job.status == status.lower())
    return query.order_by(Job.created_at.desc()).all()