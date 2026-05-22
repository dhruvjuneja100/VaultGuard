from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pickle
import pandas as pd
import numpy as np
from pathlib import Path

# =============================================
# VAULTGUARD — FastAPI Backend
# Serves the fraud detection ML model via API
# =============================================

#initialize FastAPI app
app = FastAPI(
    title="VaultGuard API",
    description="AI-powered bank statement fraud detection",
    version = "1.0.0"
)

# =============================================
# CORS MIDDLEWARE
# Allows React frontend to talk to this API
# Without this, browser blocks all requests
# =============================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://localhost:3000"],
    allow_credentials = True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# =============================================
# LOAD ML MODEL ON STARTUP
# Model loads once when server starts
# Not on every request — that would be slow
# =============================================

MODEL_PATH = Path(__file__).parent.parent.parent / "ml"/ "fraud_model.pkl"

#Load teh trainded model
with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)
print(f"Model Loaded from {MODEL_PATH}")
# =============================================
# REQUEST/RESPONSE MODELS
# Pydantic validates incoming data automatically
# If data is wrong type, FastAPI returns error
# =============================================
class StatementFeatures(BaseModel):
    """Features extracted from a bank statment.
    these match exactly what our model expects"""
    round_number_ratio:      float
    salary_is_round:         int
    salary_variance:         float
    min_balance:             float
    avg_balance:             float
    balance_variance:        float
    transaction_count:       int
    avg_debit:               float
    large_transaction_ratio: float
    credit_debit_ratio:      float

class FraudAnalysisResponse(BaseModel):
    """Response returned to the frontend"""
    risk_score:      float   # 0-100
    verdict:         str     # HIGH/MEDIUM/LOW RISK
    is_fraud:        bool    # True or False
    confidence:      float   # Model confidence %
    flags:           list    # List of fraud signals found
# =============================================
# ROUTES (API Endpoints)
# =============================================

@app.get("/")
def root():
    """Welcome endpoint — confirms API is running"""
    return {
        "message": "Welcome to VaultGuard API",
        "version": "1.0.0",
        "status":  "running"
    }
@app.get("/health")
def health_check():
    """Health check — used by deployment platforms"""
    return {
        "status":       "healthy",
        "model_loaded": model is not None
    }
@app.post("/analyze", response_model=FraudAnalysisResponse)
def analyze_statement(features: StatementFeatures):
    """
    Main endpoint — analyzes bank statement features
    and returns fraud risk score.

    Accepts: StatementFeatures (JSON)
    Returns: FraudAnalysisResponse (JSON)
    """

    # Convert incoming data to DataFrame
    # Model expects a DataFrame, not a Pydantic object
    input_data = pd.DataFrame([{
         "round_number_ratio":      features.round_number_ratio,
        "salary_is_round":         features.salary_is_round,
        "salary_variance":         features.salary_variance,
        "min_balance":             features.min_balance,
        "avg_balance":             features.avg_balance,
        "balance_variance":        features.balance_variance,
        "transaction_count":       features.transaction_count,
        "avg_debit":               features.avg_debit,
        "large_transaction_ratio": features.large_transaction_ratio,
        "credit_debit_ratio":      features.credit_debit_ratio
    }])
    # Get fraud probability from model
    # predict_proba returns [[legit_prob, fraud_prob]]
    probabilities = model.predict_proba(input_data)[0]
    fraud_probability = probabilities[1]

    # Calculate risk score (0-100)
    risk_score = round(fraud_probability * 100, 1)

    # Determine verdict
    if risk_score >= 70:
        verdict = "HIGH RISK"
    elif risk_score >= 40:
        verdict = "MEDIUM RISK"
    else:
        verdict = "LOW RISK"

    # Detect specific fraud flags
    flags = []
    if features.round_number_ratio > 0.5:
        flags.append("High round number ratio in transactions")
    if features.salary_is_round == 1:
        flags.append("Salary is suspiciously round number")
    if features.salary_variance == 0:
        flags.append("Salary never varies - no TDS deduction detected")
    if features.min_balance > 20000:
        flags.append("Minimum balance artificially high")
    if features.avg_balance > 70000:
        flags.append("Average balance suspiciously high")

    return FraudAnalysisResponse(
        risk_score=risk_score,
        verdict=verdict,
        is_fraud=fraud_probability >= 0.5,
        confidence=round(max(probabilities) * 100, 1),
        flags=flags
    )
from fastapi import UploadFile, File, HTTPException
import tempfile
import os
from backend.app.pdf_forensics import analyze_full_statement

@app.post("/analyze-pdf")
async def analyze_pdf(file: UploadFile = File(...)):
    """
    New endpoint — accepts PDF upload and runs
    full forensics + ML analysis on it.
    
    UploadFile = FastAPI's file upload handler
    File(...)  = required file field
    async      = handles file I/O asynchronously
    """

    # Validate file type
    # Only accept PDF files
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are accepted"
        )

    # Save uploaded file temporarily
    # We need a real file path for PyMuPDF
    # tempfile creates a temporary file that
    # auto-deletes when we're done
    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix='.pdf'
    ) as tmp_file:
        # Read uploaded file contents
        contents = await file.read()
        # Write to temporary file
        tmp_file.write(contents)
        tmp_path = tmp_file.name
        # tmp_path = something like C:/Temp/tmpXXXX.pdf

    try:
        # Run full forensics analysis
        analysis = analyze_full_statement(tmp_path)

        # Get features and run ML model
        features    = analysis["features"]
        features_df = pd.DataFrame([features])

        # Get fraud probability
        probabilities     = model.predict_proba(features_df)[0]
        fraud_probability = probabilities[1]
        risk_score        = round(fraud_probability * 100, 1)

        # Combine with forensics risk
        forensics_risk = analysis["forensics_risk"]
        combined_score = min(100, risk_score + (forensics_risk * 0.3))

        # Determine verdict
        if combined_score >= 70:
            verdict = "HIGH RISK"
        elif combined_score >= 40:
            verdict = "MEDIUM RISK"
        else:
            verdict = "LOW RISK"

        # Build flags list
        flags = analysis["forensics_findings"].copy()
        if features["round_number_ratio"] > 0.5:
            flags.append("High round number ratio")
        if features["salary_is_round"] == 1:
            flags.append("Salary is suspiciously round")
        if features["salary_variance"] == 0:
            flags.append("Salary never varies - no TDS detected")
        if features["min_balance"] > 20000:
            flags.append("Minimum balance artificially high")

        return {
            "filename":        file.filename,
            "risk_score":      round(combined_score, 1),
            "ml_score":        risk_score,
            "forensics_score": forensics_risk,
            "verdict":         verdict,
            "is_fraud": bool(combined_score >= 70),
            "confidence":      round(max(probabilities) * 100, 1),
            "flags":           flags,
            "transactions_found": analysis["transaction_count"],
            "fonts_detected":  analysis["fonts"]["fonts_detected"]
        }

    finally:
        # Always delete temporary file
        # finally block runs even if error occurs
        os.unlink(tmp_path)
        # os.unlink deletes a file