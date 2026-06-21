import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text
from app.database import Base

class Job(Base):
    __tablename__ = "jobs"

    # Ensure primary_key=True is typed exactly like this
    id = Column(String, primary_key=True, index=True) 
    filename = Column(String, nullable=False)
    status = Column(String, default="pending", nullable=False) 
    row_count_raw = Column(Integer, default=0)
    row_count_clean = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)