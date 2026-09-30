import uuid
import shutil
import logging
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from ..config import settings
from ..schemas import ChatRequest, ChatResponse, StructuredProductData
from ..services.reasoning_service import answer_product_doubt
from ..services.stt_service import transcribe_audio_file
from ..services.parser_service import parse_packaging_text

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Multilingual Chat & RAG"])

@router.post("/message", response_model=ChatResponse)
async def chat_message(req: ChatRequest):
    """
    Consumer doubt resolution endpoint:
    Infers language directly from user query -> Queries RAG -> Generates LLM response.
    """
    struct_data = req.structured_data or StructuredProductData()
    from ..services.reasoning_service import detect_language_style
    
    inferred_lang = detect_language_style(req.query)
    
    resp_text, is_violation, viol_item, clauses = answer_product_doubt(
        query=req.query,
        structured_data=struct_data,
        conversation_history=req.conversation_history,
        preferred_language=inferred_lang
    )

    return ChatResponse(
        response=resp_text,
        original_query=req.query,
        detected_language=inferred_lang,
        cited_clauses=clauses,
        potential_violation_detected=is_violation,
        violation_details=viol_item
    )

@router.post("/voice", response_model=ChatResponse)
async def voice_doubt(
    audio: UploadFile = File(...),
    session_id: str = Form(...),
    raw_ocr_text: str = Form(""),
    language_code: str = Form("hi-IN"),
    structured_data: str = Form(None)
):
    """
    Accepts spoken audio voice query from user in Indian languages (Hindi, Tamil, etc.).
    Transcribes audio -> Queries RAG -> Generates compliance response.
    """
    session_dir = settings.UPLOAD_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    audio_path = session_dir / f"voice_{uuid.uuid4().hex[:8]}.wav"

    with open(audio_path, "wb") as buffer:
        shutil.copyfileobj(audio.file, buffer)

    # 1. Transcribe voice audio (Sarvam Saarika API / SpeechRecognition)
    transcribed_text, detected_lang = transcribe_audio_file(str(audio_path), language_code)

    # 2. Parse structured data: use client-provided structured_data if available
    struct_data = None
    if structured_data:
        try:
            import json
            struct_dict = json.loads(structured_data)
            struct_data = StructuredProductData(**struct_dict)
        except Exception as e:
            logger.warning(f"Could not load structured_data in voice query: {e}")

    if not struct_data:
        struct_data = parse_packaging_text(raw_ocr_text)

    # 3. Formulate legal RAG response with auto-inferred language
    from ..services.reasoning_service import detect_language_style
    inferred_lang = detect_language_style(transcribed_text) if transcribed_text else (detected_lang[:2] if detected_lang else "en")

    resp_text, is_violation, viol_item, clauses = answer_product_doubt(
        query=transcribed_text,
        structured_data=struct_data,
        conversation_history=[],
        preferred_language=inferred_lang
    )

    return ChatResponse(
        response=resp_text,
        original_query=transcribed_text,
        detected_language=inferred_lang,
        cited_clauses=clauses,
        potential_violation_detected=is_violation,
        violation_details=viol_item
    )
