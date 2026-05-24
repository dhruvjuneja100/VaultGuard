from fastapi import FastAPI, UploadFile, File, HTTPException, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
from backend.app.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    Token,
    User,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from backend.app.pdf_forensics import analyze_full_statement
import pickle
import pandas as pd
import numpy as np
import tempfile
import os

# =============================================
# VAULTGUARD — FastAPI Backend
# =============================================

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="VaultGuard API",
    description="AI-powered bank statement fraud detection",
    version="1.0.0"
)

# =============================================
# RATE LIMITING
# =============================================
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler
)

# =============================================
# CORS MIDDLEWARE
# =============================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================
# LOAD ML MODEL
# =============================================
MODEL_PATH = Path(__file__).parent.parent.parent / "ml" / "fraud_model.pkl"

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

print(f"✅ Model loaded from {MODEL_PATH}")

# =============================================
# PYDANTIC MODELS
# =============================================

class StatementFeatures(BaseModel):
    """Features extracted from a bank statement"""
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
    risk_score:  float
    verdict:     str
    is_fraud:    bool
    confidence:  float
    flags:       list


# =============================================
# ROUTES
# =============================================

@app.get("/")
def root():
    return {
        "message": "Welcome to VaultGuard API",
        "version": "1.0.0",
        "status":  "running"
    }


@app.get("/health")
def health_check():
    return {
        "status":       "healthy",
        "model_loaded": model is not None
    }


@app.post("/token", response_model=Token)
@limiter.limit("5/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """Login — returns JWT token"""
    try:
        print(f"Login attempt: {form_data.username}")

        user = authenticate_user(
            form_data.username,
            form_data.password
        )
        print(f"Auth result: {user}")

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = create_access_token(
            data={"sub": form_data.username},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        return Token(
            access_token=access_token,
            token_type="bearer"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Login error: {str(e)}"
        )


@app.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Returns current logged in user info"""
    return {
        "username": current_user.username,
        "message":  "You are authenticated!"
    }


@app.post("/analyze", response_model=FraudAnalysisResponse)
@limiter.limit("10/minute")
async def analyze_statement(
    request: Request,
    features: StatementFeatures,
    current_user: User = Depends(get_current_user)
):
    """Analyze bank statement features for fraud"""

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

    probabilities     = model.predict_proba(input_data)[0]
    fraud_probability = probabilities[1]
    risk_score        = round(fraud_probability * 100, 1)

    if risk_score >= 70:
        verdict = "HIGH RISK"
    elif risk_score >= 40:
        verdict = "MEDIUM RISK"
    else:
        verdict = "LOW RISK"

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
        is_fraud=bool(fraud_probability >= 0.5),
        confidence=round(float(max(probabilities) * 100), 1),
        flags=flags
    )


@app.post("/analyze-pdf")
@limiter.limit("10/minute")
async def analyze_pdf(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Accept PDF upload and run full forensics + ML analysis"""

    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are accepted"
        )

    # Save to temp file
    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix='.pdf'
    ) as tmp_file:
        contents = await file.read()

        # Validate file size
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="File too large — max 10MB"
            )

        tmp_file.write(contents)
        tmp_path = tmp_file.name

    try:
        analysis = analyze_full_statement(tmp_path)

        # Validate transactions found
        if analysis["transaction_count"] < 5:
            raise HTTPException(
                status_code=400,
                detail="Not enough transactions found — please upload a valid bank statement"
            )

        features    = analysis["features"]
        features_df = pd.DataFrame([features])

        probabilities     = model.predict_proba(features_df)[0]
        fraud_probability = probabilities[1]
        risk_score        = round(fraud_probability * 100, 1)

        forensics_risk = analysis["forensics_risk"]
        combined_score = min(100, risk_score + (forensics_risk * 0.3))

        if combined_score >= 70:
            verdict = "HIGH RISK"
        elif combined_score >= 40:
            verdict = "MEDIUM RISK"
        else:
            verdict = "LOW RISK"

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
            "filename":           file.filename,
            "risk_score":         round(float(combined_score), 1),
            "ml_score":           float(risk_score),
            "forensics_score":    int(forensics_risk),
            "verdict":            verdict,
            "is_fraud":           bool(combined_score >= 70),
            "confidence":         round(float(max(probabilities) * 100), 1),
            "flags":              flags,
            "transactions_found": analysis["transaction_count"],
            "fonts_detected":     analysis["fonts"]["fonts_detected"]
        }

    finally:
        os.unlink(tmp_path)