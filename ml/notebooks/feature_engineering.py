import pandas as pd
import numpy as np

pd.set_option('display.max_columns',None)
pd.set_option('display.width',None)

# =============================================
# VAULTGUARD — Feature Engineering
# Transform raw transactions into ML features
# One row per statement instead of per transaction
# =============================================

#Load raw transaction data
df = pd.read_csv("data/bank_statements.csv")
print("=== RAW DATA (before feature engineering) ===")
print(f"Shape: {df.shape}")
print(f"One row = one TRANSACTION")
print(df.head(3))
print()

# =============================================
# FEATURE ENGINEERING FUNCTION
# =============================================

def engineer_features(df):
    features_list = []
     # Group transactions by statement
    # This gives us all transactions for one statement at a time
    for statement_id, group in df.groupby("statement_id"):

        #separate credits and debits
        credits = group[group["credit"]>0]["credit"]
        debits = group[group["debit"]>0]["debit"]

        #feature 1: round number ratio
        if len(debits)>0:
            round_ratio = (debits%100 ==0).mean()
        else:
            round_ratio = 0

        #feature 2: Salary is round
        salary = group[group["description"] == "SALARY CREDIT"]["credit"]
        if len(salary) > 0:
            salary_is_round = int(salary.iloc[0]%1000 == 0)
        else:
            salary_is_round =0

        #feature 3 salary variance
        if len(salary)>1:
            salary_variance = salary.std()
        else:
            salary_variance = 0

        #feature 4 minimum balance
        min_balance = group["balance"].min()
        #feature 5 average balance
        avg_balance = group["balance"].mean()
        #feature 6 balance variance
        balance_variance = group["balance"].std()
        #feature 7 transaction count
        transaction_count =  len(group)
        #average debit feature 8
        if len(debits)>0:
            avg_debit = debits.mean()
        else:
            avg_debit = 0
        
        #feature 9 large transaction ratio
        if len(debits) > 0:
            large_ratio = (debits > 10000).mean()
        else:
            large_ratio = 0
        # ── Feature 10: Credit Debit Ratio ──
        # Ratio of total credits to total debits
        total_credit = credits.sum()
        total_debit  = debits.sum()
        if total_debit > 0:
            credit_debit_ratio = total_credit / total_debit
        else:
            credit_debit_ratio = 1
            # ── Label ──
        # is_fraud is same for all transactions in a statement
        is_fraud = group["is_fraud"].iloc[0]

        # Combine all features into one row
        features_list.append({
            "statement_id":        statement_id,
            "round_number_ratio":  round_ratio,
            "salary_is_round":     salary_is_round,
            "salary_variance":     salary_variance,
            "min_balance":         min_balance,
            "avg_balance":         avg_balance,
            "balance_variance":    balance_variance,
            "transaction_count":   transaction_count,
            "avg_debit":           avg_debit,
            "large_transaction_ratio": large_ratio,
            "credit_debit_ratio":  credit_debit_ratio,
            "is_fraud":            is_fraud
        })

    return pd.DataFrame(features_list)
# =============================================
# RUN FEATURE ENGINEERING
# =============================================

print("Running feature engineering...")
features_df = engineer_features(df)

print("=== FEATURES (after feature engineering) ===")
print(f"Shape: {features_df.shape}")
print(f"One row = one STATEMENT")
print(features_df.head(3))
print()
legit_features = features_df[features_df["is_fraud"] == 0]
fraud_features = features_df[features_df["is_fraud"] == 1]

print("=== FEATURE COMPARISON ===")
print(f"{'Feature':<25} {'Legitimate':>15} {'Fraudulent':>15}")
print("-" * 55)

features_to_compare = [
    "round_number_ratio",
    "salary_is_round",
    "min_balance",
    "avg_balance",
    "avg_debit",
    "transaction_count"
]

for feature in features_to_compare:
    legit_val = legit_features[feature].mean()
    fraud_val = fraud_features[feature].mean()
    print(f"{feature:<25} {legit_val:>15.2f} {fraud_val:>15.2f}")

print()

# =============================================
# SAVE FEATURES FOR ML MODEL
# =============================================

features_df.to_csv("data/features.csv", index=False)
print(f"✅ Features saved to data/features.csv")
print(f"   Shape: {features_df.shape}")
print(f"   Ready for ML model training!")