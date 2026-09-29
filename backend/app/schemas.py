from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

# --- Label Extraction Schemas ---
class NutritionFacts(BaseModel):
    energy_kcal: Optional[float] = None
    protein_g: Optional[float] = None
    carbohydrates_g: Optional[float] = None
    total_sugars_g: Optional[float] = None
    added_sugars_g: Optional[float] = None
    dietary_fiber_g: Optional[float] = None
    total_fat_g: Optional[float] = None
    saturated_fat_g: Optional[float] = None
    trans_fat_g: Optional[float] = None
    sodium_mg: Optional[float] = None
    raw_nutrition_text: Optional[str] = ""

class StructuredProductData(BaseModel):
    product_name: str = "Unknown Product"
    brand: str = "Unknown Brand"
    primary_language: str = "en"
    detected_scripts: List[str] = Field(default_factory=list)
    ingredients: List[str] = Field(default_factory=list)
    nutrition: NutritionFacts = Field(default_factory=NutritionFacts)
    veg_nonveg: Optional[str] = "UNKNOWN" # "VEG", "NON_VEG", "UNKNOWN"
    fssai_license: Optional[str] = None
    batch_number: Optional[str] = None
    mfg_date: Optional[str] = None
    expiry_date: Optional[str] = None
    net_quantity: Optional[str] = None
    mrp: Optional[str] = None
    customer_care: Optional[str] = None
    claims: List[str] = Field(default_factory=list)
    allergen_advice: Optional[str] = None

# --- Audit & Violation Schemas ---
class ComplianceCheckItem(BaseModel):
    rule_id: str
    regulation: str
    section: str
    title: str
    status: str # "PASS", "FAIL", "WARNING", "INCONCLUSIVE"
    severity: str # "CRITICAL", "MAJOR", "MINOR", "INFO"
    evidence: str
    statutory_clause: str
    confidence: float

class AuditSummary(BaseModel):
    total_checks: int
    passed_checks: int
    failed_checks: int
    warning_checks: int
    overall_status: str # "COMPLIANT", "SUSPECTED_VIOLATION", "NON_COMPLIANT"
    overall_confidence: float
    items: List[ComplianceCheckItem]

class AuditResponse(BaseModel):
    session_id: str
    image_urls: List[str]
    raw_ocr_text: str
    structured_data: StructuredProductData
    audit: AuditSummary

# --- Chat & RAG Schemas ---
class ChatMessage(BaseModel):
    role: str # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None
    cited_clauses: Optional[List[Dict[str, Any]]] = None

class ChatRequest(BaseModel):
    session_id: str
    query: str
    language: Optional[str] = "en" # "hi", "ta", "te", "en", etc.
    structured_data: Optional[StructuredProductData] = None
    conversation_history: List[ChatMessage] = Field(default_factory=list)

class ChatResponse(BaseModel):
    response: str
    original_query: str
    detected_language: str
    cited_clauses: List[Dict[str, Any]]
    potential_violation_detected: bool
    violation_details: Optional[ComplianceCheckItem] = None

# --- Incident Deliberation Schemas ---
class IncidentCreateRequest(BaseModel):
    session_id: str
    product_name: Optional[str] = None
    brand: Optional[str] = None
    image_urls: List[str] = Field(default_factory=list)
    raw_ocr_text: str = ""
    structured_data: Dict[str, Any] = Field(default_factory=dict)
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    flagged_violations: List[Dict[str, Any]] = Field(default_factory=list)
    severity: str = "MAJOR"
    confidence_score: float = 0.85
    user_notes: Optional[str] = None

class IncidentUpdateRequest(BaseModel):
    status: Optional[str] = None # PENDING_REVIEW, UNDER_DELIBERATION, VERIFIED_VIOLATION, DISMISSED, ESCALATED_FSSAI
    officer_notes: Optional[str] = None
    severity: Optional[str] = None

class IncidentReportResponse(BaseModel):
    id: int
    report_uuid: str
    product_name: str
    brand: str
    fssai_license: Optional[str]
    batch_number: Optional[str]
    status: str
    severity: str
    confidence_score: float
    image_paths: List[str]
    raw_ocr_text: str
    structured_data: Dict[str, Any]
    conversation_history: List[Dict[str, Any]]
    flagged_violations: List[Dict[str, Any]]
    officer_notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
