import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
# =============================================
# VAULTGUARD — Synthetic Data Generator
# Generates realistic legitimate and fraudulent
# bank statements for ML model training
# =============================================
random.seed(42)
np.random.seed(42)

def generate_legitimate_statement(statement_id, months=3):
    """
    Generate a realistic LEGITIMATE bank statement.
    
    Legitimate statements have:
    - Salary with slight variations (TDS deductions)
    - Odd amount transactions (real spending)
    - Natural balance fluctuations
    - Transactions on working days mostly
    """
    transactions = []

    # Real salary vaires slightly every month due to tds

    base_salary = random.randint(30000,80000)

    # start date is 'months' agao from today
    start_date = datetime.now() - timedelta(days = months*30)
    current_date = start_date
    # starting balance - real people have varied starting balances
    balance = random.randint(2000,15000)
    
    while current_date < datetime.now():
        #salary credited on 1st of every month
        if current_date.day ==1:
            tds_deduction = random.randint(200,900)
            salary = base_salary - tds_deduction

            balance += salary
            transactions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "description": "SALARY CREDIT",
                "credit": salary,
                "debit": 0,
                "balance": balance,
                "is_fraud":0
            })
        #Random daily transactions
        #60% chance of at least one trasaction per day
        if random.random() >0.4:
            #real spending has odd amounts - never perfectly round
            amount = random.randint(100,5000)
            amount = amount + random.randint(1,99)

            if balance > amount:
                balance -= amount
                transactions.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "description": random.choice([
                        "UPI Payment",
                        "ATM Withdrawal",
                        "Online Purchase",
                        "Utility Bill",
                        "Grocery",
                        "Fuel",
                        "Medical",
                        "Restaurant"
                    ]),
                    "credit": 0,
                    "debit": amount,
                    "balance": balance,
                    "is_fraud": 0
                })
        current_date += timedelta(days=1)
    #add statement id to every transactions
    df = pd.DataFrame(transactions)
    df["statement_id"] = statement_id
    return df

def generate_fraudulent_statement(statement_id, months=3):
    """
    Generate a FRAUDULENT bank statement.

    Fraudulent statements have:
    - Perfectly round salary (no TDS deduction)
    - Round number transactions (manually typed)
    - Suspiciously stable balance
    - Salary higher than realistic
    """
    transactions = []

    # Fraudster inflates salary — always picks a round number
    fake_salary = random.choice([50000, 60000, 75000, 100000])

    start_date = datetime.now() - timedelta(days=months * 30)
    current_date = start_date

    balance = random.choice([5000,75000,100000])
    while current_date <datetime.now():
        if current_date.day == 1:
            balance += fake_salary
            transactions.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "description": "SALARY CREDIT",
            "credit": fake_salary,
            "debit": 0,
            "balance": balance,
            "is_fraud": 1
        })
        # Fraudster adds fake transactions — always round numbers
        if random.random() > 0.5:
            amount = random.choice([
                500, 1000, 2000, 5000, 10000
            ])  # Always round!

            if balance > amount:
                balance -= amount
                transactions.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "description": random.choice([
                        "UPI Payment",
                        "Online Transfer",
                        "ATM Withdrawal"
                    ]),
                    "credit": 0,
                    "debit": amount,
                    "balance": balance,
                    "is_fraud": 1
                })

        current_date += timedelta(days=1)

    df = pd.DataFrame(transactions)
    df["statement_id"] = statement_id
    return df

# =============================================
# GENERATE THE FULL DATASET
# =============================================

print("generating synthetic bank statments.....")
print()

all_statements = []

# generate 50 legitimate statements
for i in range(50):
    statement = generate_legitimate_statement(statement_id=f"LEGIT_{i:03d}")
    all_statements.append(statement)

#generate 50 fraud statments
for i in range(50):
    statement = generate_fraudulent_statement(
        statement_id=f"FRAUD_{i:03d}"
    )
    all_statements.append(statement)

full_dataset = pd.concat(all_statements,ignore_index = True)
full_dataset.to_csv("data/bank_statements.csv", index=False)

# =============================================
# PRINT SUMMARY
# =============================================
print(f" Dataset created successfully!")
print()
print(f"Total transactions:      {len(full_dataset):,}")
print(f"Total statements:        100")
print(f"Legitimate statements:   50")
print(f"Fraudulent statements:   50")
print()
print(f"Legitimate transactions: {len(full_dataset[full_dataset['is_fraud']==0]):,}")
print(f"Fraudulent transactions: {len(full_dataset[full_dataset['is_fraud']==1]):,}")
print()
print("Sample legitimate transaction:")
print(full_dataset[full_dataset["is_fraud"]==0].head(3))
print()
print("Sample fraudulent transaction:")
print(full_dataset[full_dataset["is_fraud"]==1].head(3))
