from fastapi import FastAPI,UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pdf2image import convert_from_path
from pypdf import PdfReader
import os
import requests
from openai import OpenAI
from dotenv import load_dotenv
import pytesseract
import fitz
from PIL import Image

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
client = OpenAI()
upload_folder = os.path.join(os.path.dirname(__file__), "uploads")

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
from database import create_tables, get_connection
from models import Bidder, Requirement,Tender,Bid,Requirement, VerificationResult

app = FastAPI(title="Satyam")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
create_tables()

def extract_pdf_text(file_path):
    reader = PdfReader(file_path)

    text = ""

    for page in reader.pages:
        text += page.extract_text() or ""

    # If PDF has no readable text, use OCR
    if not text.strip():
        pdf = fitz.open(file_path)

        for page in pdf:
            pix = page.get_pixmap(dpi=200)

            image = Image.frombytes(
                "RGB",
                [pix.width, pix.height],
                pix.samples
            )

            text += pytesseract.image_to_string(image)

        pdf.close()

    return text

def extract_ocr_text(file_path):
    images = convert_from_path(file_path, dpi=300)

    text = ""

    for image in images:
        text += pytesseract.image_to_string(image)

    return text

@app.get("/")
def home():
    return {
        "status": "success",
        "message": "Satyam Backend Running"
    }


@app.get("/api/health")
def health():
    return {
        "status": "success",
        "message": "Satyam Backend Healthy"
    }
@app.post("/api/bidders")
def add_bidder(bidder: Bidder):
    connection = get_connection()

    cursor = connection.execute(
        """
        INSERT INTO bidders (company_name, gstin, pan, udyam_number)
        VALUES (?, ?, ?, ?)
        """,
        (
            bidder.company_name,
            bidder.gstin,
            bidder.pan,
            bidder.udyam_number
        )
    )

    connection.commit()

    bidder_id = cursor.lastrowid

    connection.close()

    return {
        "status": "success",
        "message": "Bidder added successfully",
        "bidder_id": bidder_id
    }

@app.get("/api/bidders")
def get_bidders():
    connection = get_connection()

    bidders = connection.execute(
        "SELECT * FROM bidders"
    ).fetchall()

    connection.close()

    return [dict(bidder) for bidder in bidders]
@app.post("/api/bids")
def add_bid(bid: Bid):
    connection = get_connection()

    cursor = connection.execute(
        """
        INSERT INTO bids (bidder_id, tender_id, bid_amount)
        VALUES (?, ?, ?)
        """,
        (bid.bidder_id, bid.tender_id, bid.bid_amount)
    )

    connection.commit()
    connection.close()

    return {
        "status": "success",
        "message": "Bid added successfully",
        "bid_id": cursor.lastrowid
    }
@app.get("/api/bids")
def get_bids():
    connection = get_connection()

    bids = connection.execute(
        "SELECT * FROM bids"
    ).fetchall()

    connection.close()

    return [dict(bid) for bid in bids]
@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    bidder_id: int = Form(...)
):

    os.makedirs(upload_folder, exist_ok=True)

    file_path = os.path.join(upload_folder, file.filename)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    connection = get_connection()

    cursor = connection.execute(
    """
    INSERT INTO documents (bidder_id, file_name, file_path)
    VALUES (?, ?, ?)
    """,
    (bidder_id, file.filename, file_path)
) 

    connection.commit()
    connection.close()

    return {
        "status": "success",
        "message": "Document uploaded successfully",
        "document_id": cursor.lastrowid,
        "file_name": file.filename,
        "file_path": file_path
    }
@app.get("/api/documents")
def get_documents():
    connection = get_connection()

    documents = connection.execute(
        "SELECT * FROM documents"
    ).fetchall()

    connection.close()

    return [dict(document) for document in documents]

@app.post("/api/requirements")
def add_requirement(requirement:Requirement):
    connection = get_connection()

    cursor = connection.execute(
        """
        INSERT INTO requirements (tender_id, requirement_text, requirement_type)
        VALUES (?, ?, ?)
        """,
        (
            requirement.tender_id,
            requirement.requirement_text,
            requirement.requirement_type
        )
    )

    connection.commit()
    connection.close()

    return {
        "status": "success",
        "message": "Requirement added successfully",
        "requirement_id": cursor.lastrowid
    }
@app.get("/api/requirements")
def get_requirements():
    connection = get_connection()

    requirements = connection.execute(
        "SELECT * FROM requirements"
    ).fetchall()

    connection.close()

    return [dict(requirement) for requirement in requirements]
@app.post("/api/verification")
def add_verification(result: VerificationResult):
    connection = get_connection()

    cursor = connection.execute(
        """
        INSERT INTO verification_results
        (requirement_id, document_id, status, confidence, reason)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            result.requirement_id,
            result.document_id,
            result.status,
            result.confidence,
            result.reason
        )
    )

    connection.commit()
    connection.close()

    return {
        "status": "success",
        "message": "Verification result added successfully",
        "verification_id": cursor.lastrowid
    }
@app.get("/api/verification")
def get_verifications():
    connection = get_connection()

    verifications = connection.execute(
        "SELECT * FROM verification_results"
    ).fetchall()

    connection.close()

    return [dict(verification) for verification in verifications]

def get_document_text(document_id: int):
    connection = get_connection()

    document = connection.execute(
        "SELECT * FROM documents WHERE id = ?",
        (document_id,)
    ).fetchone()

    connection.close()

    if document is None:
        return {
            "status": "error",
            "message": "Document not found",
            "text": ""
        }

    return {
        "status": "success",
        "document_id": document_id,
        "file_name": document["file_name"],
        "text": extract_pdf_text(document["file_path"])
    }

@app.get("/api/documents/{document_id}/text")
def read_document_text(document_id: int):
    connection = get_connection()

    document = connection.execute(
        "SELECT * FROM documents WHERE id = ?",
        (document_id,)
    ).fetchone()

    connection.close()

    if document is None:
        return {"status": "error", "message": "Document not found"}

    text = extract_pdf_text(document["file_path"])

    return {
        "status": "success",
        "document_id": document_id,
        "file_name": document["file_name"],
        "text": text
    }
@app.get("/api/verify/{document_id}/{requirement_id}")
def verify_document(document_id: int, requirement_id: int):

    connection = get_connection()

    # Get document
    document = connection.execute(
        "SELECT * FROM documents WHERE id = ?",
        (document_id,)
    ).fetchone()

    if document is None:
        connection.close()
        return {
            "status": "error",
            "message": "Document not found"
        }

    # Get requirement
    requirement = connection.execute(
        "SELECT * FROM requirements WHERE id = ?",
        (requirement_id,)
    ).fetchone()

    if requirement is None:
        connection.close()
        return {
            "status": "error",
            "message": "Requirement not found"
        }

    connection.close()

    # Extract PDF text
    text = extract_pdf_text(document["file_path"])

    if not text:
        return {
            "status": "error",
            "message": "Could not extract text from document"
        }

    text_lower = text.lower()
    requirement_text = requirement["requirement_text"].lower()

    # GST verification
    if requirement["requirement_type"].upper() == "GST":

        gst_keywords = [
            "gst",
            "goods and services tax",
            "gstin",
            "gst registration"
        ]

        found = any(keyword in text_lower for keyword in gst_keywords)

        if found:
            status = "PASS"
            confidence = 0.90
            reason = "GST-related information was found in the document."
        else:
            status = "FAIL"
            confidence = 0.90
            reason = "GST registration information was not found in the document."

    else:
        status = "REVIEW"
        confidence = 0.50
        reason = "Automatic verification for this requirement type is not implemented yet."

    return {
        "status": "success",
        "document_id": document_id,
        "requirement_id": requirement_id,
        "requirement": requirement["requirement_text"],
        "verification_status": status,
        "confidence": confidence,
        "reason": reason
    }


@app.get("/api/tenders")
def get_tenders():
    connection = get_connection()

    tenders = connection.execute(
        "SELECT * FROM tenders"
    ).fetchall()

    connection.close()

    return [dict(tender) for tender in tenders]
   
    connection.commit()
    tender_id = cursor.lastrowid
    connection.close()

    return {
        "status": "success",
        "message": "Tender added successfully",
        "tender_id": tender_id
    }
@app.post("/api/tenders")
def add_tender(tender: Tender):

    connection = get_connection()

    cursor = connection.execute(
        """
        INSERT INTO tenders
        (tender_name, tender_number, title, description)
        VALUES (?, ?, ?, ?)
        """,
        (
            tender.title,
            tender.tender_number,
            tender.title,
            tender.description
        )
    )

    connection.commit()

    tender_id = cursor.lastrowid

    connection.close()

    return {
        "status": "success",
        "message": "Tender added successfully",
        "tender_id": tender_id
    }
@app.get("/api/risk/{bidder_id}")
def calculate_risk(bidder_id: int):

    connection = get_connection()

    results = connection.execute(
        """
        SELECT verification_results.status,
               verification_results.confidence
        FROM verification_results
        JOIN documents
        ON verification_results.document_id = documents.id
        WHERE documents.bidder_id = ?
        """,
        (bidder_id,)
    ).fetchall()

    connection.close()

    if not results:
        return {
            "status": "success",
            "bidder_id": bidder_id,
            "risk_score": 0,
            "risk_level": "LOW",
            "message": "No verification issues found"
        }

    risk_score = 0

    for result in results:

        if result["status"] == "FAIL":
            risk_score += 50

        elif result["status"] == "REVIEW":
            risk_score += 25

        elif result["status"] == "PASS":
            risk_score += 0

    if risk_score >= 50:
        risk_level = "HIGH"

    elif risk_score >= 25:
        risk_level = "MEDIUM"

    else:
        risk_level = "LOW"

    return {
        "status": "success",
        "bidder_id": bidder_id,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "verification_count": len(results)
    }
@app.post("/api/audit")
def add_audit_log(
    action: str,
    entity_type: str,
    entity_id: int,
    details: str
):
    connection = get_connection()

    cursor = connection.execute(
        """
        INSERT INTO audit_logs
        (action, entity_type, entity_id, details)
        VALUES (?, ?, ?, ?)
        """,
        (action, entity_type, entity_id, details)
    )

    connection.commit()

    audit_id = cursor.lastrowid

    connection.close()

    return {
        "status": "success",
        "message": "Audit log added successfully",
        "audit_id": audit_id
    }
@app.get("/api/audit")
def get_audit_logs():
    connection = get_connection()

    logs = connection.execute(
        """
        SELECT *
        FROM audit_logs
        ORDER BY id DESC
        """
    ).fetchall()

    connection.close()

    return [dict(log) for log in logs]


    connection = get_connection()

    results = connection.execute(
        """
        SELECT v.status, v.confidence
        FROM verification_results v
        JOIN documents d ON v.document_id = d.id
        WHERE d.bidder_id = ?
        """,
        (bidder_id,)
    ).fetchall()

    connection.close()

    if not results:
        return {
            "bidder_id": bidder_id,
            "risk_score": 0,
            "risk_level": "LOW",
            "message": "No verification records found"
        }

    risk_score = 0

    for result in results:

        if result["status"] == "FAIL":
            risk_score += 50

        elif result["status"] == "REVIEW":
            risk_score += 25

        elif result["status"] == "PASS":
            risk_score += 0

    if risk_score >= 50:
        risk_level = "HIGH"

    elif risk_score >= 25:
        risk_level = "MEDIUM"

    else:
        risk_level = "LOW"

    return {
        "bidder_id": bidder_id,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "verification_count": len(results)
    }
@app.get("/api/final-decision/{bidder_id}")
def final_decision(bidder_id: int):

    risk = calculate_risk(bidder_id)

    if risk["risk_level"] == "HIGH":
        decision = "REJECT"

    elif risk["risk_level"] == "MEDIUM":
        decision = "REVIEW"

    else:
        decision = "APPROVE"

    return {
        "bidder_id": bidder_id,
        "risk_score": risk["risk_score"],
        "risk_level": risk["risk_level"],
        "verification_count": risk.get("verification_count", 0),
        "final_decision": decision
    }
@app.get("/api/ai-compliance/{document_id}/{requirement_id}")
def ai_compliance(document_id: int, requirement_id: int):

    connection = get_connection()

    requirement = connection.execute(
        "SELECT * FROM requirements WHERE id = ?",
        (requirement_id,)
    ).fetchone()

    document = connection.execute(
        "SELECT * FROM documents WHERE id = ?",
        (document_id,)
    ).fetchone()

    connection.close()

    if not requirement:
        return {"status": "error", "message": "Requirement not found"}

    if not document:
        return {"status": "error", "message": "Document not found"}

    # Get OCR text
    text_result = get_document_text(document_id)

    if isinstance(text_result, dict):
        document_text = text_result.get("text", "")
    else:
        document_text = str(text_result)

    prompt = f"""
You are SATYAM, an AI procurement compliance verification system.

Tender Requirement:
{requirement["requirement_text"]}

Document Content:
{document_text[:12000]}

Determine whether the document satisfies the tender requirement.

Return ONLY valid JSON in this exact format:
{{
  "status": "PASS",
  "confidence": 0.95,
  "reason": "Short explanation based on the document evidence."
}}

Allowed status values:
PASS
FAIL
REVIEW
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )

        response.raise_for_status()

        ai_response = response.json()["response"].strip()

        # Remove markdown code fences if Qwen adds them
        ai_response = ai_response.replace("```json", "").replace("```", "").strip()

        import json
        result = json.loads(ai_response)

        status = result.get("status", "REVIEW")
        confidence = float(result.get("confidence", 0.5))
        reason = result.get("reason", "AI analysis completed.")

    except Exception as e:
        return {
            "status": "error",
            "message": "Local AI analysis failed",
            "error": str(e)
        }

    connection = get_connection()

    cursor = connection.execute(
        """
        INSERT INTO verification_results
        (requirement_id, document_id, status, confidence, reason)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            requirement_id,
            document_id,
            status,
            confidence,
            reason
        )
    )

    verification_id = cursor.lastrowid

    connection.execute(
        """
        INSERT INTO audit_logs
        (action, entity_type, entity_id, details)
        VALUES (?, ?, ?, ?)
        """,
        (
            "ai_compliance",
            "document",
            document_id,
            f"Local Qwen AI verification completed. Requirement ID: {requirement_id}, Status: {status}"
        )
    )

    connection.commit()
    connection.close()

    return {
        "status": "success",
        "document_id": document_id,
        "requirement_id": requirement_id,
        "verification_id": verification_id,
        "compliance_status": status,
        "confidence": confidence,
        "reason": reason,
        "ai_model": OLLAMA_MODEL,
        "message": "Local AI compliance result saved to database and audit trail"
    }
def ask_satyam_ai(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen2.5:3b",
            "prompt": prompt,
            "stream": False
        }
    )

    response.raise_for_status()

    return response.json()["response"]
from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


@app.post("/api/login")
def login(data: LoginRequest):

    if data.email == "admin@satyam.gov.in" and data.password == "satyam123":
        return {
            "status": "success",
            "message": "Login successful",
            "user": {
                "name": "SATYAM Officer",
                "role": "Procurement Officer"
            }
        }

    return {
        "status": "error",
        "message": "Invalid email or password"
    }
    
