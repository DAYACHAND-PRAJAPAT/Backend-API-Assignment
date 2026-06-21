import datetime
from app.worker import celery_app
from app.database import SessionLocal
from app.models.job import Job
from app.models.transaction import Transaction
from app.models.summary import JobSummary
from app.services.data_cleaner import DataCleaner
from app.services.anomaly_detector import AnomalyDetector
from app.services.llm_client import LLMClient

@celery_app.task(name="app.tasks.process_csv_pipeline", bind=True)
def process_csv_pipeline(self, job_id: str, file_bytes: bytes):
    """
    Background worker function running the end-to-end 5-step processing pipeline.
    """
    db = SessionLocal()
    
    # 1. Update Job status to 'processing'
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        db.close()
        return f"Job {job_id} not found in database."
        
    job.status = "processing"
    db.commit()
    
    try:
        # Step A: Data Cleaning
        cleaner = DataCleaner()
        df_clean, raw_count, clean_count = cleaner.clean_csv(file_bytes)
        
        job.row_count_raw = raw_count
        job.row_count_clean = clean_count
        db.commit()

        # Step B: Anomaly Detection
        detector = AnomalyDetector()
        df_analyzed = detector.detect_anomalies(df_clean)

        # Step C: LLM Classification (Batching uncategorised entries)
        llm = LLMClient()
        category_mapping = llm.batch_classify_categories(df_analyzed)
        
        # Apply LLM classifications and flag fallbacks if the batch call failed
        llm_failed_flag = len(category_mapping) == 0 and (df_analyzed['category'] == 'Uncategorised').any()
        
        for idx, row in df_analyzed.iterrows():
            final_cat = row['category']
            llm_cat = None
            
            if row['category'] == 'Uncategorised' and idx in category_mapping:
                final_cat = category_mapping[idx]
                llm_cat = category_mapping[idx]

            # Save clean row record to database array
            txn_record = Transaction(
                job_id=job_id,
                txn_id=None if str(row['txn_id']) == 'nan' or not str(row['txn_id']).strip() else str(row['txn_id']),
                date=row['date'],
                merchant=row['merchant'],
                amount=float(row['amount']),
                currency=row['currency'],
                status=row['status'],
                category=final_cat,
                account_id=row['account_id'],
                is_anomaly=bool(row['is_anomaly']),
                anomaly_reason=row['anomaly_reason'] if row['is_anomaly'] else None,
                llm_category=llm_cat,
                llm_raw_response="Processed in batch mode" if llm_cat else None,
                llm_failed=llm_failed_flag if row['category'] == 'Uncategorised' else False
            )
            db.add(txn_record)
        
        db.commit()

        # Step D: LLM Narrative Summary
        summary_data = llm.generate_narrative_summary(df_analyzed)
        
        if summary_data:
            # Save the narrative breakdown safely
            summary_record = JobSummary(
                job_id=job_id,
                total_spend_inr=float(summary_data.get('total_spend_by_currency', {}).get('INR', 0.0)),
                total_spend_usd=float(summary_data.get('total_spend_by_currency', {}).get('USD', 0.0)),
                top_merchants=summary_data.get('top_3_merchants', []),
                anomaly_count=int(summary_data.get('anomaly_count', int(df_analyzed['is_anomaly'].sum()))),
                narrative=summary_data.get('spending_narrative', "Summary narrative generated successfully."),
                risk_level=summary_data.get('risk_level', 'medium').lower()
            )
            db.add(summary_record)
        else:
            # Fallback local schema save if narrative generation failed completely
            summary_record = JobSummary(
                job_id=job_id,
                total_spend_inr=float(df_analyzed[df_analyzed['currency'] == 'INR']['amount'].sum()),
                total_spend_usd=float(df_analyzed[df_analyzed['currency'] == 'USD']['amount'].sum()),
                top_merchants=df_analyzed['merchant'].value_counts().head(3).index.tolist(),
                anomaly_count=int(df_analyzed['is_anomaly'].sum()),
                narrative="LLM narrative generation timed out or failed.",
                risk_level="medium"
            )
            db.add(summary_record)

        # Mark core job as completed successfully
        job.status = "completed"
        job.completed_at = datetime.datetime.utcnow()
        db.commit()

    except Exception as e:
        db.rollback()
        job.status = "failed"
        job.error_message = str(e)
        job.completed_at = datetime.datetime.utcnow()
        db.commit()
    finally:
        db.close()