import sys
import os

# Add project root to Python path
# So we can import from backend/app/
# Without this, Python can't find pdf_forensics.py
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.app.pdf_forensics import analyze_full_statement
import pickle
import pandas as pd

# =============================================
# VAULTGUARD — Forensics Test Script
# Tests our PDF forensics engine on both
# legitimate and fraudulent test PDFs
# =============================================

# Load our trained ML model
with open("ml/fraud_model.pkl", "rb") as f:
    model = pickle.load(f)

print("✅ ML Model loaded")
print()


def analyze_and_predict(pdf_path: str, label: str):
    """
    Run full forensics + ML prediction on a PDF.
    
    pdf_path → path to PDF file
    label    → "LEGITIMATE" or "FRAUDULENT" 
               (so we know if model was correct)
    """

    print(f"{'='*60}")
    print(f"Testing: {label} statement")
    print(f"File: {pdf_path}")
    print(f"{'='*60}")

    # Run full forensics analysis
    # Returns: features, forensics_risk, findings etc.
    analysis = analyze_full_statement(pdf_path)

    # Get ML features from analysis
    features = analysis["features"]

    # Convert features dict to DataFrame
    # Model expects DataFrame not plain dict
    features_df = pd.DataFrame([features])

    # Get fraud probability from ML model
    probabilities      = model.predict_proba(features_df)[0]
    fraud_probability  = probabilities[1]
    risk_score         = round(fraud_probability * 100, 1)

    # Combine ML risk + forensics risk
    # ML gives 0-100, forensics gives 0-75
    # We blend them for final score
    forensics_risk  = analysis["forensics_risk"]
    combined_score  = min(100, risk_score + (forensics_risk * 0.3))
    # min(100,...) ensures score never exceeds 100
    # forensics * 0.3 gives forensics 30% weight

    # Determine verdict
    if combined_score >= 70:
        verdict = "🔴 HIGH RISK"
    elif combined_score >= 40:
        verdict = "🟡 MEDIUM RISK"
    else:
        verdict = "🟢 LOW RISK"

    # Print results
    print(f"\n=== ML ANALYSIS ===")
    print(f"Fraud probability:  {fraud_probability*100:.1f}%")
    print(f"ML risk score:      {risk_score}/100")

    print(f"\n=== FORENSICS ANALYSIS ===")
    print(f"Forensics risk:     {forensics_risk}/75")

    if analysis["forensics_findings"]:
        print("Forensics findings:")
        for finding in analysis["forensics_findings"]:
            print(f"  ⚠️  {finding}")
    else:
        print("  ✅ No forensics issues found")

    print(f"\n=== FINAL VERDICT ===")
    print(f"Combined score:     {combined_score:.1f}/100")
    print(f"Verdict:            {verdict}")
    print(f"Transactions found: {analysis['transaction_count']}")

    # Check if prediction matches expected label
    is_fraud_predicted = combined_score >= 70
    is_fraud_actual    = label == "FRAUDULENT"

    if is_fraud_predicted == is_fraud_actual:
        print(f"\n✅ CORRECT — Model prediction matches actual label!")
    else:
        print(f"\n❌ WRONG — Model prediction doesn't match!")

    print()
    return combined_score


# ── Run tests on both PDFs ──
legit_score = analyze_and_predict(
    "data/test_pdfs/legitimate_statement.pdf",
    "LEGITIMATE"
)

fraud_score = analyze_and_predict(
    "data/test_pdfs/fraudulent_statement.pdf",
    "FRAUDULENT"
)

# ── Final Summary ──
print(f"{'='*60}")
print(f"SUMMARY")
print(f"{'='*60}")
print(f"Legitimate statement score: {legit_score:.1f}/100")
print(f"Fraudulent statement score: {fraud_score:.1f}/100")
print()

if fraud_score > legit_score:
    print("✅ System correctly scores fraud HIGHER than legitimate!")
else:
    print("⚠️  Something went wrong — check extraction logic")