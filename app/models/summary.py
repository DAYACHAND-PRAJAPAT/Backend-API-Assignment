from sqlalchemy import Column, String, Float, Integer, JSON, Text, ForeignKey
from app.database import Base

class JobSummary(Base):
    __tablename__ = "job_summaries"

    id = Column(Integer, primary_key=True, autoincrement=True) #[cite: 66]
    job_id = Column(String, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, unique=True) #[cite: 66]
    total_spend_inr = Column(Float, default=0.0) #[cite: 66]
    total_spend_usd = Column(Float, default=0.0) #[cite: 66]
    top_merchants = Column(JSON, nullable=False) # Stores Top 3 list [cite: 67]
    anomaly_count = Column(Integer, default=0) #[cite: 67]
    narrative = Column(Text, nullable=False) #[cite: 67]
    risk_level = Column(String, nullable=False) # low/medium/high [cite: 52, 67]