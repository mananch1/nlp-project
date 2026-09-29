import uuid
import shutil
import logging
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from ..config import settings
from ..schemas import AuditResponse
from ..services.ocr_service import extract_text_from_images
from ..services.parser_service import parse_packaging_text
from ..services.auditor_service import run_baseline_compliance_audit

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/audit", tags=["Audit & OCR"])

@router.post("/upload", response_model=AuditResponse)
async def upload_and_audit(files: List[UploadFile] = File(...)):
    """
    Accepts 1 to 5 packaging photos.
    Runs Open-Source local OCR -> Multi-stage NLP parsing -> Immediate FSSAI Baseline Compliance Audit.
    """
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="At least 1 packaging image is required.")
    if len(files) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 packaging images allowed.")

    session_id = str(uuid.uuid4())
    session_dir = settings.UPLOAD_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    saved_paths = []
    image_urls = []

    for idx, file in enumerate(files):
        ext = Path(file.filename).suffix or ".jpg"
        target_path = session_dir / f"image_{idx+1}{ext}"
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_paths.append(str(target_path))
        # Relative URL for static serving
        image_urls.append(f"/static/uploads/{session_id}/image_{idx+1}{ext}")

    logger.info(f"Session {session_id}: Saved {len(saved_paths)} images. Starting OCR...")

    # 1. OCR Extraction across uploaded photos
    raw_ocr_text, ocr_details = extract_text_from_images(saved_paths)

    # 2. Multi-Stage NLP Parsing
    structured_data = parse_packaging_text(raw_ocr_text)

    # 3. Baseline Compliance Audit
    audit_summary = run_baseline_compliance_audit(structured_data)

    return AuditResponse(
        session_id=session_id,
        image_urls=image_urls,
        raw_ocr_text=raw_ocr_text,
        structured_data=structured_data,
        audit=audit_summary
    )

@router.post("/audit-text", response_model=AuditResponse)
async def audit_text(payload: dict):
    """
    Audits raw text directly (for showcase test cases and direct evaluation).
    """
    raw_ocr_text = payload.get("text", "")
    session_id = payload.get("session_id", str(uuid.uuid4()))
    image_url = payload.get("image_url")
    
    structured_data = parse_packaging_text(raw_ocr_text)
    audit_summary = run_baseline_compliance_audit(structured_data)
    
    return AuditResponse(
        session_id=session_id,
        image_urls=[image_url] if image_url else [],
        raw_ocr_text=raw_ocr_text,
        structured_data=structured_data,
        audit=audit_summary
    )

