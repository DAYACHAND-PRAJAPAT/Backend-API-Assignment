from sqlalchemy import Column, String, Float, Boolean, Text, ForeignKey, Integer
from app.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)  # cite: 62
    job_id = Column(String, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)  # cite: 62
    txn_id = Column(String, nullable=True)  # Some rows are intentionally blank | cite: 20, 62
    date = Column(String, nullable=False)  # Normalized ISO format | cite: 43, 62
    merchant = Column(String, nullable=False)  # cite: 62
    amount = Column(Float, nullable=False)  # cite: 62
    currency = Column(String, nullable=False)  # cite: 62
    status = Column(String, nullable=False)  # Normalized uppercase | cite: 43, 63
    category = Column(String, nullable=False)  # Original or 'Uncategorised' | cite: 43, 63
    account_id = Column(String, nullable=False)  # cite: 63

    # Validation & Detection Metadata
    is_anomaly = Column(Boolean, default=False)  # cite: 64
    anomaly_reason = Column(Text, nullable=True)  # cite: 64
    llm_category = Column(String, nullable=True)  # cite: 64
    llm_raw_response = Column(Text, nullable=True)  # cite: 64
    llm_failed = Column(Boolean, default=False)  # cite: 64