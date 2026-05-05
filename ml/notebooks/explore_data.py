import pandas as pd
import numpy as np

pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

# =============================================
# VAULTGUARD — Dataset Exploration
# Understanding our generated data before
# building the ML model
# =============================================

#Load the dataset we generated
df = pd.read_csv("data/bank_statements.csv")
print("--- DATASET OVERVIEW --- ")
print(f"Total Transactions: {len(df):,}")
print(f"Columns: {df.columns.tolist()}")
print(f"Date range: {df['date'].min()} to {df['date'].max()}")
print()

# =============================================
# PART 1 — Compare Legitimate vs Fraud
# =============================================

legit =df[df["is_fraud"] == 0]
fraud = df[df["is_fraud"] ==1]
print("--Legitimate vs fraud comparision---")
print(f"{'Metric':<30}{'Legitimate':>15}{'Fraudulent':>15}")
print("-"*60)
print(f"{'Total transactions':<30} {len(legit):>15,} {len(fraud):>15,}")
print(f"{'Avg debit amount':<30} {legit['debit'].mean():>15.0f} {fraud['debit'].mean():>15.0f}")
print(f"{'Avg credit amount':<30} {legit['credit'].mean():>15.0f} {fraud['credit'].mean():>15.0f}")
print(f"{'Avg balance':<30} {legit['balance'].mean():>15.0f} {fraud['balance'].mean():>15.0f}")
print()

# =============================================
# PART 2 — Round Number Analysis
# =============================================
print("==ROUND NUMBER ANALYSIS==")
legit_debits = legit[legit["debit"]>0]["debit"]
fraud_debits = fraud[fraud["debit"]>0]["debit"]

legit_round = (legit_debits % 100 ==0).mean()*100
fraud_round = (fraud_debits % 100 ==0).mean()*100

print(f"Legitimate round number ratio: {legit_round:.1f}%")
print(f"Fraudulent round number ratio: {fraud_round:.1f}%")
print()

if fraud_round > legit_round:
    print(f"Round number ratio successfully distinguishes fraud!")
    print(f"Fraud has {fraud_round - legit_round:.1f}% more round numbers")
else:
    print("Round number ratio not distinguishing well")
print()
# =============================================
# PART 3 — Salary Analysis
# =============================================
print("===Salary analysis===")

legit_salary = legit[legit["description"] == "SALARY CREDIT"]["credit"]
fraud_salary = fraud[fraud["description"] == "SALARY CREDIT"]["credit"]

print(f"Legitimate salary — avg: ₹{legit_salary.mean():,.0f}, "
      f"std: ₹{legit_salary.std():,.0f}")
print(f"Fraudulent salary — avg: ₹{fraud_salary.mean():,.0f}, "
      f"std: ₹{fraud_salary.std():,.0f}")
print()
legit_round_salary = (legit_salary % 1000 == 0).mean() * 100
fraud_round_salary  = (fraud_salary % 1000 == 0).mean() * 100

print(f"Legitimate round salaries: {legit_round_salary:.1f}%")
print(f"Fraudulent round salaries: {fraud_round_salary:.1f}%")
print()

# =============================================
# PART 4 — Balance Analysis
# =============================================
print("=== BALANCE ANALYSIS ===")
print(f"Legitimate min balance: ₹{legit['balance'].min():,}")
print(f"Fraudulent min balance: ₹{fraud['balance'].min():,}")
print()
print(f"Legitimate avg balance: ₹{legit['balance'].mean():,.0f}")
print(f"Fraudulent avg balance: ₹{fraud['balance'].mean():,.0f}")
print()
# =============================================
# PART 5 — Key Findings Summary
# =============================================
print("=== KEY FINDINGS — What ML Model Will Learn ===")
print()
print("These differences between legitimate and fraud")
print("are the SIGNALS our ML model will detect:")
print()
print(f"1. Round number ratio:")
print(f"   Legitimate: {legit_round:.0f}% vs Fraud: {fraud_round:.0f}%")
print()
print(f"2. Round salary ratio:")
print(f"   Legitimate: {legit_round_salary:.0f}% vs Fraud: {fraud_round_salary:.0f}%")
print()
print(f"3. Average balance:")
print(f"   Legitimate: ₹{legit['balance'].mean():,.0f} "
      f"vs Fraud: ₹{fraud['balance'].mean():,.0f}")
print()
