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