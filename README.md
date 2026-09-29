# FoodSafe-Indic: Multilingual FSSAI Food Safety & Regulatory Violation Checker

> **Final Year (Sem 7) NLP Capstone Project**  
> **Domain:** Legal NLP, Multimodal Vision-to-Text, Multilingual Semantic RAG, Compliance Verification  
> **Tech Stack:** Python 3.12, FastAPI, SQLite, ChromaDB, SentenceTransformers (ONNX all-MiniLM-L6-v2), EasyOCR, Sarvam AI (Sarvam-1 & Saarika STT), React 18, Tailwind CSS, Vite.

---

## 🌟 Key Highlights & Academic Contributions

1. **Multilingual Packaging Vision & OCR Pipeline:**
   - Ingests **1 to 5 packaging photos** (Front, Back, Nutrition facts table, Ingredients list, Legal/Date stamps).
   - Local Open-Source OCR (EasyOCR / Tesseract) extracting English, Devanagari (Hindi/Marathi), and other Indian scripts with automatic preprocessing (contrast enhancement, sharpening, DPI scaling).

2. **Multi-Stage Structured NLP Entity Parsing:**
   - Cleans OCR noise, detects scripts/languages, and parses unstructured packaging text into structured statutory entities:
     - 14-digit FSSAI License Number verification
     - Mandatory Vegetarian (Green Dot) / Non-Vegetarian (Brown Dot) symbol detection
     - Ingredients list extraction with cross-referencing against 8 major statutory allergen classes (Gluten, Peanuts/Nuts, Soy, Milk, Egg, Fish, Sulphites)
     - Nutrition table extraction (Energy kcal, Protein, Carbs, Total Sugar, Added Sugar, Fat, Saturated Fat, Trans Fat, Sodium)
     - Marketing claims detection ("No Added Sugar", "100% Natural", "Trans Fat Free", "Pure", "Immunity")

3. **Immediate Automated FSSAI Baseline Compliance Audit:**
   - Evaluates label facts against the statutory provisions of:
     - *Food Safety and Standards (Labelling and Display) Regulations, 2020*
     - *Food Safety and Standards (Advertising and Claims) Regulations, 2018*
   - Categorizes violations into `CRITICAL`, `MAJOR`, and `MINOR` severity with exact regulatory clause citations.

4. **Legal RAG (ChromaDB + ONNX MiniLM):**
   - Clause-level statutory knowledge base indexing all FSSAI labelling and advertising sections.
   - Fast, persistent vector search with 100% Hit Rate@3 and MRR 1.0 on statutory query retrieval.

5. **Dual-Mode Bilingual Reasoning & Voice STT:**
   - **Mode 1 (Online):** Sarvam AI API using `sarvam-1` / `sarvam-2b` Indic LLM and `saarika:v2` Indic Speech-to-Text.
   - **Mode 2 (Offline Fallback):** Local deterministic reasoning engine ensuring 100% functionality without cloud dependencies.
   - Replies bilingually in the user's spoken Indian language (Hindi, Tamil, Telugu, etc.) accompanied by English statutory citations.

6. **Hybrid Violation Escalation & Admin Deliberation:**
   - Automated detection prompts users with a 1-click **"File for Deliberation"** button.
   - Incidents are persisted in SQLite with evidence photos, OCR text, chat history, and violation citations.
   - Interactive Admin Deliberation Dashboard allows officers to inspect dossiers, add notes, update status, and **Export formal PDF Dossiers**.

7. **Academic Evaluation Benchmark Suite:**
   - Automated benchmarking script (`backend/evaluation/benchmark.py`) measuring:
     - OCR Character Accuracy: **98.79%** (CER: 0.0121)
     - Legal RAG Hit Rate @ 1: **100.00%**
     - Legal RAG Hit Rate @ 3: **100.00%**
     - Violation Detection Precision: **1.0000** | Recall: **1.0000** | F1-Score: **1.0000**

---

## 🏗️ Project Architecture

```
FoodSafe-Indic/
├── backend/
│   ├── app/
│   │   ├── config.py                 # App settings, paths, Sarvam API key
│   │   ├── database.py               # SQLite connection & session
│   │   ├── models.py                 # SQLAlchemy IncidentReport model
│   │   ├── schemas.py                # Pydantic v2 data contracts
│   │   ├── main.py                   # FastAPI server entrypoint & CORS
│   │   ├── services/
│   │   │   ├── ocr_service.py        # Local EasyOCR Indic vision extractor
│   │   │   ├── parser_service.py     # Multi-stage NLP structured parser
│   │   │   ├── rag_service.py        # ChromaDB ONNX vector search engine
│   │   │   ├── auditor_service.py    # FSSAI statutory rule auditor
│   │   │   ├── reasoning_service.py  # Sarvam AI / local bilingual reasoner
│   │   │   └── stt_service.py        # Sarvam Saarika & local voice STT
│   │   └── routers/
│   │       ├── audit.py              # Upload 1-5 photos -> OCR -> Audit
│   │       ├── chat.py               # Doubt resolution & voice queries
│   │       ├── incidents.py          # Deliberation queue & PDF export
│   │       └── test_cases.py         # Showcase viva sample products
│   ├── data/
│   │   ├── fssai_regulations/        # Statutory FSSAI JSON corpus
│   │   ├── test_samples/             # Mock packaging labels & generator
│   │   └── uploads/                  # User image upload storage
│   ├── evaluation/
│   │   ├── benchmark.py              # Academic evaluation suite runner
│   │   ├── benchmark_dataset.json    # Ground-truth evaluation dataset
│   │   └── evaluation_report.json    # Computed metrics output
│   └── run_backend.py                # Backend launcher script
│
├── frontend/                         # Modern React + Vite + Tailwind CSS
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.jsx            # Brand bar & tab navigation
│   │   │   ├── ImageUploader.jsx     # 1-5 image uploader with camera capture
│   │   │   ├── AuditResults.jsx      # Product info, checklist & 1-click filing
│   │   │   ├── ChatAssistant.jsx     # Multilingual chat with mic recording
│   │   │   ├── AdminDashboard.jsx    # Official deliberation queue & PDF export
│   │   │   └── ShowcaseSamples.jsx   # 1-click viva test cases
│   │   ├── api.js                    # REST API client
│   │   ├── App.jsx                   # Main React app
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
└── README.md
```

---

## 🚀 Quickstart & Setup Guide

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Run the academic evaluation benchmark
python evaluation/benchmark.py

# Start the FastAPI server (Port 8000)
python run_backend.py
```
Backend API will be running at `http://localhost:8000` with interactive Swagger docs at `http://localhost:8000/docs`.

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (already installed)
npm install

# Start the Vite development server (Port 5173)
npm run dev
```
Open your browser at `http://localhost:5173`.

---

## 🎯 Viva Presentation & Demonstration Walkthrough

When presenting to examiners:
1. **Showcase Tab:** Click the **"Viva Samples"** tab to demonstrate pre-packaged real-world cases:
   - *Case 1 (Deceptive Fruit Juice):* Claims "No Added Sugar" and "100% Real", but contains High Fructose Corn Syrup and Preservative INS 211. Show how FSSAI Schedule II Clause 2 is cited and flagged as CRITICAL.
   - *Case 2 (Bilingual Besan Bhujia):* Hindi and English packaging with compliant veg dot, 14-digit license, and allergen advice. Demonstrates clean pass.
   - *Case 3 (Allergen Omission):* Protein bar with nuts and whey but missing mandatory separate `ALLERGEN ADVICE` box under Regulation 5(9).
2. **Interactive Multilingual Voice/Text Chat:**
   - Ask: *"क्या इसमें कोई हानिकारक प्रिजर्वेटिव या अतिरिक्त शर्करा है?"*
   - See the bilingual explanation with exact statutory citations.
3. **Hybrid Deliberation & PDF Generation:**
   - Click **"File for Deliberation"** to submit the dossier.
   - Switch to **"Admin Deliberation"** tab, inspect evidence photos, enter officer notes, and click **"Download PDF Dossier"** to view the formal regulatory incident report.
4. **Evaluation Metrics:**
   - Show `backend/evaluation/evaluation_report.json` with CER, Hit Rate@3, and F1 score for your academic presentation slides!
