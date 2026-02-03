from sqlalchemy import Column, Integer, Float, String, DateTime
from datetime import datetime
from .session import Base

class YieldRecord(Base):
    __tablename__ = "yield_records"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    healthy_count = Column(Integer)
    damaged_count = Column(Integer)
    total_count = Column(Integer)
    health_index = Column(Float)  # (healthy / total) * 100
    created_at = Column(DateTime, default=datetime.utcnow)