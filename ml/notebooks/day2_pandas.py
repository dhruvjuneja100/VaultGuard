import pandas as pd

# Display settings — show all columns and full width
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

# =============================================
# VAULTGUARD — Bank Statement Fraud Analysis
# Day 2: Pandas Fundamentals + Fraud Detection
# =============================================

# Sample bank statement data
# In the real system, this will be extracted from a PDF
data = {
    "date": [
        "2024-01-01",
        "2024-01-02",
        "2024-01-03",
        "2024-01-04",
        "2024-01-05"
    ],
    "description": [
        "Salary Credit",
        "Rent Payment",
        "Grocery",
        "ATM Withdrawal",
        "Online Transfer"
    ],
    "amount":  [50000, 20000, 1500, 10000, 5000],
    "balance": [50000, 30000, 28500, 18500, 13500],
    "type":    ["credit", "debit", "debit", "debit", "debit"]
}

# Create DataFrame and convert date column to datetime
df = pd.DataFrame(data)
df["date"] = pd.to_datetime(df["date"])

# =============================================
# PART 1 — Basic Exploration
# =============================================

print("=== Bank Statement DataFrame ===")
print(df)
print()

print("=== Shape (rows, columns) ===")
print(df.shape)
print()

print("=== Data Types ===")
print(df.dtypes)
print()

print("=== Basic Statistics ===")
print(f"Total money moved:   ₹{df['amount'].sum():,}")
print(f"Average transaction: ₹{df['amount'].mean():,.0f}")
print(f"Largest transaction: ₹{df['amount'].max():,}")
print(f"Smallest transaction:₹{df['amount'].min():,}")
print()

# =============================================
# PART 2 — Filtering Data
# =============================================

print("=== Debit Transactions Only ===")
debits = df[df["type"] == "debit"]
print(debits)
print()

print("=== Transactions Above ₹10,000 ===")
large_transactions = df[df["amount"] > 10000]
print(large_transactions)
print()

# =============================================
# PART 3 — Fraud Detection Checks
# =============================================

print("=== FRAUD CHECK 1: Round Number Analysis ===")
round_transactions = df[df["amount"] % 1000 == 0]
round_ratio = len(round_transactions) / len(df) * 100
print(f"Total transactions:       {len(df)}")
print(f"Round number transactions:{len(round_transactions)}")
print(f"Round number ratio:       {round_ratio:.1f}%")
if round_ratio > 50:
    print("⚠️  WARNING: High round number ratio — suspicious!")
else:
    print("✅ Round number ratio looks normal")
print()

print("=== FRAUD CHECK 2: Salary Analysis ===")
salary = df[df["description"] == "Salary Credit"]
print(f"Number of salary credits: {len(salary)}")
print(f"Salary amounts: {salary['amount'].tolist()}")
print()

for amount in salary["amount"]:
    if amount % 1000 == 0:
        print(f"⚠️  WARNING: Salary ₹{amount:,} is a perfectly round number!")
        print("    Real salaries have TDS deductions — never perfectly round")
    else:
        print(f"✅ Salary ₹{amount:,} looks legitimate")
print()

print("=== FRAUD CHECK 3: Balance Analysis ===")
print(f"Minimum balance: ₹{df['balance'].min():,}")
print(f"Maximum balance: ₹{df['balance'].max():,}")
print(f"Balance variance: ₹{df['balance'].std():,.2f}")
if df["balance"].min() > 10000:
    print("⚠️  WARNING: Balance never drops below ₹10,000 — possibly artificial")
else:
    print("✅ Balance pattern looks normal")
print()

# =============================================
# PART 4 — Overall Risk Score
# =============================================

print("=== OVERALL FRAUD RISK SCORE ===")
risk_score = 0
reasons = []

# Check 1 — Round number ratio
if round_ratio > 50:
    risk_score += 30
    reasons.append("High round number ratio (+30)")

# Check 2 — Round salary
if len(salary) > 0 and salary["amount"].iloc[0] % 1000 == 0:
    risk_score += 40
    reasons.append("Perfectly round salary (+40)")

# Check 3 — Minimum balance
if df["balance"].min() > 10000:
    risk_score += 30
    reasons.append("Suspiciously high minimum balance (+30)")

# Print reasons
for reason in reasons:
    print(f"⚠️  {reason}")

print()
print(f"🔴 FRAUD RISK SCORE: {risk_score}/100")
print()

if risk_score >= 70:
    print("VERDICT: HIGH RISK — Recommend manual review")
elif risk_score >= 40:
    print("VERDICT: MEDIUM RISK — Additional verification needed")
else:
    print("VERDICT: LOW RISK — Appears legitimate")