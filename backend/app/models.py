from datetime import datetime
import json
from sqlalchemy import Column, Integer, String, Text, Float, DateTime
from .database import Base

class IncidentReport(Base):
    __tablename__ = "incident_reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    report_uuid = Column(String(64), unique=True, index=True, nullable=False)
    product_name = Column(String(255), default="Unknown Product")
    brand = Column(String(255), default="Unknown Brand")
    fssai_license = Column(String(32), default="")
    batch_number = Column(String(64), default="")
    
    # Status: PENDING_REVIEW, UNDER_DELIBERATION, VERIFIED_VIOLATION, DISMISSED, ESCALATED_FSSAI
    status = Column(String(32), default="PENDING_REVIEW", index=True)
    
    # Severity: CRITICAL, MAJOR, MINOR, COMPLIANT
    severity = Column(String(32), default="MINOR")
    confidence_score = Column(Float, default=0.0)
    
    # Storage of complex fields as JSON strings
    image_paths_json = Column(Text, default="[]")
    raw_ocr_text = Column(Text, default="")
    structured_data_json = Column(Text, default="{}")
    conversation_history_json = Column(Text, default="[]")
    flagged_violations_json = Column(Text, default="[]")
    
    # Deliberation field
    officer_notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def image_paths(self):
        try:
            return json.loads(self.image_paths_json or "[]")
        except Exception:
            return []

    @image_paths.setter
    def image_paths(self, value):
        self.image_paths_json = json.dumps(value)

    @property
    def structured_data(self):
        try:
            return json.loads(self.structured_data_json or "{}")
        except Exception:
            return {}

    @structured_data.setter
    def structured_data(self, value):
        self.structured_data_json = json.dumps(value)

    @property
    def conversation_history(self):
        try:
            return json.loads(self.conversation_history_json or "[]")
        except Exception:
            return []

    @conversation_history.setter
    def conversation_history(self, value):
        self.conversation_history_json = json.dumps(value)

    @property
    def flagged_violations(self):
        try:
            return json.loads(self.flagged_violations_json or "[]")
        except Exception:
            return []

    @flagged_violations.setter
    def flagged_violations(self, value):
        self.flagged_violations_json = json.dumps(value)
