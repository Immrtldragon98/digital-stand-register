from datetime import datetime
from sqlalchemy import Column, Date, DateTime, Integer, String, Text
from app.database.session import Base

class PMActivity(Base):
    __tablename__="pm_activities"
    id=Column(Integer,primary_key=True,index=True)
    planned_date=Column(Date,nullable=False,index=True) # activity date; retained column name for compatibility
    line_name=Column(String(16),nullable=True,index=True)
    shift=Column(String(8),nullable=True)
    position_number=Column(Integer,nullable=True)
    stand_code=Column(String(50),nullable=True)
    equipment=Column(String(120),nullable=False)
    component=Column(String(100),nullable=True)
    activity_type=Column(String(60),nullable=True)
    activity=Column(String(255),nullable=False)
    from_value=Column(String(100),nullable=True)
    to_value=Column(String(100),nullable=True)
    frequency=Column(String(40),nullable=True)
    assigned_to=Column(String(100),nullable=True)
    status=Column(String(20),nullable=False,default="COMPLETED",index=True)
    completed_date=Column(Date,nullable=True)
    remarks=Column(Text,nullable=True)
    source_text=Column(Text,nullable=True)
    created_by=Column(String(100),nullable=False)
    updated_by=Column(String(100),nullable=False)
    created_at=Column(DateTime,nullable=False,default=datetime.utcnow)
    updated_at=Column(DateTime,nullable=False,default=datetime.utcnow,onupdate=datetime.utcnow)
