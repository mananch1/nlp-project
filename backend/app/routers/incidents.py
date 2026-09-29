import uuid
import io
import json
import logging
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import IncidentReport
from ..schemas import (
    IncidentCreateRequest,
    IncidentUpdateRequest,
    IncidentReportResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/incidents", tags=["Deliberation & Violations"])

@router.post("/report", response_model=IncidentReportResponse)
def create_incident_report(req: IncidentCreateRequest, db: Session = Depends(get_db)):
    """
    Submits an identified violation dossier to the backend database for deliberation.
    """
    report_uuid = f"FSSAI-INC-{uuid.uuid4().hex[:8].upper()}"
    
    struct_data = req.structured_data or {}
    product_name = req.product_name or struct_data.get("product_name", "Packaged Product")
    brand = req.brand or struct_data.get("brand", "Unspecified Brand")
    fssai_lic = struct_data.get("fssai_license", "")
    batch_no = struct_data.get("batch_number", "")

    incident = IncidentReport(
        report_uuid=report_uuid,
        product_name=product_name,
        brand=brand,
        fssai_license=fssai_lic,
        batch_number=batch_no,
        status="PENDING_REVIEW",
        severity=req.severity,
        confidence_score=req.confidence_score,
        image_paths_json=json.dumps(req.image_urls),
        raw_ocr_text=req.raw_ocr_text,
        structured_data_json=json.dumps(struct_data),
        conversation_history_json=json.dumps(req.conversation_history),
        flagged_violations_json=json.dumps(req.flagged_violations),
        officer_notes=f"User submitted note: {req.user_notes}" if req.user_notes else ""
    )
    
    db.add(incident)
    db.commit()
    db.refresh(incident)
    logger.info(f"Incident {report_uuid} successfully registered in database.")
    return incident

@router.get("", response_model=List[IncidentReportResponse])
def list_incidents(db: Session = Depends(get_db)):
    """Lists all reported incidents for the Admin Deliberation Dashboard"""
    return db.query(IncidentReport).order_by(IncidentReport.created_at.desc()).all()

@router.get("/{report_uuid}", response_model=IncidentReportResponse)
def get_incident(report_uuid: str, db: Session = Depends(get_db)):
    """Retrieves full incident details by UUID"""
    incident = db.query(IncidentReport).filter(IncidentReport.report_uuid == report_uuid).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident report not found")
    return incident

@router.patch("/{report_uuid}", response_model=IncidentReportResponse)
def update_incident(report_uuid: str, req: IncidentUpdateRequest, db: Session = Depends(get_db)):
    """Updates deliberation status and officer notes"""
    incident = db.query(IncidentReport).filter(IncidentReport.report_uuid == report_uuid).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident report not found")

    if req.status is not None:
        incident.status = req.status
    if req.severity is not None:
        incident.severity = req.severity
    if req.officer_notes is not None:
        incident.officer_notes = req.officer_notes
    incident.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(incident)
    return incident

@router.get("/{report_uuid}/pdf")
def export_incident_pdf(report_uuid: str, db: Session = Depends(get_db)):
    """Generates and downloads a formal regulatory PDF incident dossier"""
    incident = db.query(IncidentReport).filter(IncidentReport.report_uuid == report_uuid).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident report not found")

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors

        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Title Header
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(50, height - 50, "FSSAI Food Safety Compliance Incident Report")
        
        pdf.setFont("Helvetica", 10)
        pdf.setFillColor(colors.gray)
        pdf.drawString(50, height - 68, f"Dossier ID: {incident.report_uuid} | Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        pdf.setStrokeColor(colors.gray)
        pdf.line(50, height - 75, width - 50, height - 75)

        # Product Summary
        pdf.setFillColor(colors.black)
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, height - 100, "1. Product Particulars")

        pdf.setFont("Helvetica", 10)
        y = height - 120
        pdf.drawString(60, y, f"Product Name: {incident.product_name}")
        y -= 18
        pdf.drawString(60, y, f"Brand / Marketer: {incident.brand}")
        y -= 18
        pdf.drawString(60, y, f"FSSAI License No: {incident.fssai_license or 'MISSING / UNREGISTERED'}")
        y -= 18
        pdf.drawString(60, y, f"Batch Number: {incident.batch_number or 'NOT DECLARED'}")
        y -= 18
        pdf.drawString(60, y, f"Deliberation Status: {incident.status} (Severity: {incident.severity})")

        # Violations Section
        y -= 30
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y, "2. Identified Statutory Violations")
        y -= 20

        pdf.setFont("Helvetica", 10)
        violations = incident.flagged_violations
        if violations:
            for v in violations:
                pdf.setFont("Helvetica-Bold", 10)
                pdf.drawString(60, y, f"• [{v.get('section', 'General')}] {v.get('title', 'Violation')}")
                y -= 15
                pdf.setFont("Helvetica", 9)
                pdf.drawString(70, y, f"Evidence: {v.get('evidence', '')[:100]}")
                y -= 15
                pdf.drawString(70, y, f"Regulation: {v.get('regulation', '')}")
                y -= 20
        else:
            pdf.drawString(60, y, "No formal violations flagged during baseline audit.")
            y -= 20

        # Officer Deliberation Notes
        y -= 10
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y, "3. Deliberation Notes & Official Action")
        y -= 20
        pdf.setFont("Helvetica-Oblique", 10)
        notes = incident.officer_notes or "Pending officer review and regulatory deliberation."
        pdf.drawString(60, y, notes[:120])

        pdf.showPage()
        pdf.save()
        buffer.seek(0)

        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=Incident_{incident.report_uuid}.pdf"}
        )
    except Exception as e:
        logger.error(f"PDF export failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")
