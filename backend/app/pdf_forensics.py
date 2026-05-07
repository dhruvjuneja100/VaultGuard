import fitz  # PyMuPDF
import pdfplumber
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import re

# =============================================
# VAULTGUARD — PDF Forensics Engine
# Analyzes PDF bank statements for tampering
# Two layers:
# 1. PDF structure analysis (cybersecurity)
# 2. Transaction data analysis (ML features)
# =============================================


def analyze_pdf_metadata(pdf_path: str) -> dict:
    """
    Layer 1A — Analyze PDF metadata for tampering signs.
    Metadata = hidden information about the PDF file itself.
    """
    findings = []
    risk_points = 0

    # Open PDF with PyMuPDF
    doc = fitz.open(pdf_path)

    # Extract metadata
    metadata = doc.metadata

    print(f"=== PDF METADATA ===")
    print(f"Author:   {metadata.get('author', 'Unknown')}")
    print(f"Creator:  {metadata.get('creator', 'Unknown')}")
    print(f"Producer: {metadata.get('producer', 'Unknown')}")
    print(f"Created:  {metadata.get('creationDate', 'Unknown')}")
    print(f"Modified: {metadata.get('modDate', 'Unknown')}")
    print()

    # Check 1 — Was PDF modified after creation?
    creation_date = metadata.get('creationDate', '')
    mod_date = metadata.get('modDate', '')

    if creation_date and mod_date:
        if creation_date != mod_date:
            findings.append(
                "PDF was modified after original creation"
            )
            risk_points += 25

    # Check 2 — Was it created by suspicious software?
    creator = metadata.get('creator', '').lower()
    producer = metadata.get('producer', '').lower()

    suspicious_tools = [
        'adobe acrobat', 'smallpdf', 'ilovepdf',
        'pdf editor', 'nitro', 'foxit'
    ]

    for tool in suspicious_tools:
        if tool in creator or tool in producer:
            findings.append(
                f"PDF was edited using: {tool}"
            )
            risk_points += 30
            break

    # Check 3 — Does PDF have multiple edit layers?
    page_count = doc.page_count
    total_objects = 0
    for page_num in range(page_count):
        page = doc[page_num]
        # Count annotation objects (signs of editing)
        annotations = list(page.annots())
        total_objects += len(annotations)

    if total_objects > 5:
        findings.append(
            f"PDF has {total_objects} annotation objects — signs of editing"
        )
        risk_points += 20

    doc.close()

    return {
        "metadata_risk_points": risk_points,
        "metadata_findings":    findings,
        "creator":              metadata.get('creator', 'Unknown'),
        "was_modified":         creation_date != mod_date
    }


def analyze_pdf_fonts(pdf_path: str) -> dict:
    """
    Layer 1B — Analyze fonts for inconsistencies.
    Tampered PDFs often have mixed fonts from
    different source documents.
    """
    findings = []
    risk_points = 0

    doc = fitz.open(pdf_path)
    all_fonts = set()

    # Collect all fonts used in document
    for page_num in range(doc.page_count):
        page = doc[page_num]
        fonts = page.get_fonts()
        for font in fonts:
            font_name = font[3]  # Font name is at index 3
            all_fonts.add(font_name)

    print(f"=== FONT ANALYSIS ===")
    print(f"Fonts found: {all_fonts}")
    print()

    # Check — Too many different fonts?
    # Real bank statements use 1-2 fonts consistently
    # Tampered statements mix fonts from different sources
    if len(all_fonts) > 4:
        findings.append(
            f"Too many fonts detected: {len(all_fonts)} "
            f"— possible copy-paste from different sources"
        )
        risk_points += 25

    doc.close()

    return {
        "font_risk_points": risk_points,
        "font_findings":    findings,
        "fonts_detected":   list(all_fonts),
        "font_count":       len(all_fonts)
    }


def extract_transactions(pdf_path: str) -> pd.DataFrame:
    """
    Layer 2 — Extract transaction data from PDF.
    Uses pdfplumber to read text from PDF pages.
    """
    transactions = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # Extract text from page
            text = page.extract_text()

            if not text:
                continue

            # Process each line
            lines = text.split('\n')

            for line in lines:
                # Look for lines that contain amounts
                # Pattern: date + description + amount
                # Example: "01/01/2024 SALARY CREDIT 50000.00"

                # Find all numbers in the line
                numbers = re.findall(r'\d+\.\d+|\d+', line)

                if len(numbers) >= 2:
                    try:
                        # Last number is usually balance
                        # Second to last is usually amount
                        amount = float(numbers[-2])
                        balance = float(numbers[-1])

                        # Filter out header rows and tiny numbers
                        if amount > 10 and balance > 0:
                            # Determine if credit or debit
                            line_lower = line.lower()
                            is_credit = any(word in line_lower for word in [
                                'credit', 'salary', 'deposit',
                                'received', 'refund'
                            ])

                            transactions.append({
                                "raw_line":  line.strip(),
                                "amount":    amount,
                                "balance":   balance,
                                "is_credit": is_credit
                            })
                    except (ValueError, IndexError):
                        continue

    if len(transactions) == 0:
        print("⚠️  No transactions extracted from PDF")
        return pd.DataFrame()

    df = pd.DataFrame(transactions)
    print(f"✅ Extracted {len(df)} transactions from PDF")
    return df


def calculate_features(transactions_df: pd.DataFrame) -> dict:
    """
    Calculate ML features from extracted transactions.
    Same features as our training data.
    """
    if transactions_df.empty:
        # Return default features if no transactions found
        return {
            "round_number_ratio":      0.5,
            "salary_is_round":         0,
            "salary_variance":         0,
            "min_balance":             0,
            "avg_balance":             0,
            "balance_variance":        0,
            "transaction_count":       0,
            "avg_debit":               0,
            "large_transaction_ratio": 0,
            "credit_debit_ratio":      1.0
        }

    df = transactions_df
    credits = df[df["is_credit"] == True]["amount"]
    debits  = df[df["is_credit"] == False]["amount"]

    # Round number ratio
    if len(debits) > 0:
        round_ratio = float((debits % 100 == 0).mean())
    else:
        round_ratio = 0.0

    # Salary analysis
    salary = credits[credits > 10000]  # Large credits = salary
    if len(salary) > 0:
        salary_is_round  = int(salary.iloc[0] % 1000 == 0)
        salary_variance  = float(salary.std()) if len(salary) > 1 else 0.0
    else:
        salary_is_round = 0
        salary_variance = 0.0

    # Balance features
    min_balance      = float(df["balance"].min())
    avg_balance      = float(df["balance"].mean())
    balance_variance = float(df["balance"].std())

    # Transaction features
    transaction_count = len(df)
    avg_debit = float(debits.mean()) if len(debits) > 0 else 0.0

    # Large transaction ratio
    if len(debits) > 0:
        large_ratio = float((debits > 10000).mean())
    else:
        large_ratio = 0.0

    # Credit debit ratio
    total_credit = float(credits.sum())
    total_debit  = float(debits.sum())
    if total_debit > 0:
        credit_debit_ratio = total_credit / total_debit
    else:
        credit_debit_ratio = 1.0

    return {
        "round_number_ratio":      round_ratio,
        "salary_is_round":         salary_is_round,
        "salary_variance":         salary_variance,
        "min_balance":             min_balance,
        "avg_balance":             avg_balance,
        "balance_variance":        balance_variance,
        "transaction_count":       transaction_count,
        "avg_debit":               avg_debit,
        "large_transaction_ratio": large_ratio,
        "credit_debit_ratio":      credit_debit_ratio
    }


def analyze_full_statement(pdf_path: str) -> dict:
    """
    Master function — runs all forensics checks
    and returns complete analysis report.
    """
    print(f"\n{'='*50}")
    print(f"ANALYZING: {pdf_path}")
    print(f"{'='*50}\n")

    # Layer 1A — Metadata forensics
    metadata_analysis = analyze_pdf_metadata(pdf_path)

    # Layer 1B — Font forensics
    font_analysis = analyze_pdf_fonts(pdf_path)

    # Layer 2 — Extract transactions
    transactions = extract_transactions(pdf_path)

    # Calculate ML features
    features = calculate_features(transactions)

    # Combine all risk points
    total_forensics_risk = (
        metadata_analysis["metadata_risk_points"] +
        font_analysis["font_risk_points"]
    )

    # Combine all findings
    all_findings = (
        metadata_analysis["metadata_findings"] +
        font_analysis["font_findings"]
    )

    return {
        "features":          features,
        "forensics_risk":    total_forensics_risk,
        "forensics_findings": all_findings,
        "metadata":          metadata_analysis,
        "fonts":             font_analysis,
        "transaction_count": len(transactions)
    }