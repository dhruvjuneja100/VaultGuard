import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score
)
import pickle

pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

# =============================================
# VAULTGUARD — ML Model Training
# Train a Random Forest to detect fraud
# =============================================

# Load engineered features
df = pd.read_csv("data/features.csv")

print("=== DATASET INFO ===")
print(f"Total statements: {len(df)}")
print(f"Legitimate: {len(df[df['is_fraud']==0])}")
print(f"Fraudulent: {len(df[df['is_fraud']==1])}")
print()

# =============================================
# STEP 1 — Prepare X and y
# =============================================

# X = features (everything model uses to predict)
# y = label (what model is trying to predict)

# Drop columns that are NOT features
X = df.drop(["statement_id", "is_fraud"], axis=1)
y = df["is_fraud"]

print("=== FEATURES (X) ===")
print(f"Shape: {X.shape}")
print(f"Features: {X.columns.tolist()}")
print()

print("=== LABEL (y) ===")
print(f"Shape: {y.shape}")
print(f"Values: {y.value_counts().to_dict()}")
print()

# =============================================
# STEP 2 — Train/Test Split
# =============================================

# Split data: 80% for training, 20% for testing
# random_state=42 ensures same split every time
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42
)

print("=== TRAIN/TEST SPLIT ===")
print(f"Training samples: {len(X_train)} (80%)")
print(f"Testing samples:  {len(X_test)} (20%)")
print()

# =============================================
# STEP 3 — Train the Model
# =============================================

print("Training Random Forest model...")

model = RandomForestClassifier(
    n_estimators=100,   # 100 decision trees
    max_depth=10,       # Each tree max 10 levels deep
    random_state=42     # Reproducible results
)

# This is where the magic happens!
# Model learns patterns from training data
model.fit(X_train, y_train)

print("✅ Model trained successfully!")
print()

# =============================================
# STEP 4 — Evaluate the Model
# =============================================

# Make predictions on TEST data
# Model has never seen this data before
y_pred = model.predict(X_test)

print("=== MODEL PERFORMANCE ===")
print(f"Accuracy: {accuracy_score(y_test, y_pred)*100:.1f}%")
print()

print("=== DETAILED REPORT ===")
print(classification_report(y_test, y_pred,
      target_names=["Legitimate", "Fraud"]))

print("=== CONFUSION MATRIX ===")
cm = confusion_matrix(y_test, y_pred)
print(f"                 Predicted")
print(f"                 Legit  Fraud")
print(f"Actual  Legit  [{cm[0][0]:>5}  {cm[0][1]:>5}]")
print(f"        Fraud  [{cm[1][0]:>5}  {cm[1][1]:>5}]")
print()

# =============================================
# STEP 5 — Feature Importance
# =============================================

print("=== FEATURE IMPORTANCE ===")
print("(Which signals matter most to the model?)")
print()

importance_df = pd.DataFrame({
    "feature":   X.columns,
    "importance": model.feature_importances_
}).sort_values("importance", ascending=False)

for _, row in importance_df.iterrows():
    bar = "█" * int(row["importance"] * 50)
    print(f"{row['feature']:<25} {row['importance']:.3f} {bar}")
print()

# =============================================
# STEP 6 — Test on a Real Example
# =============================================

print("=== REAL WORLD TEST ===")

# Simulate a suspicious statement
suspicious = pd.DataFrame([{
    "round_number_ratio":      1.0,    # 100% round numbers
    "salary_is_round":         1,      # Round salary
    "salary_variance":         0,      # No salary variation
    "min_balance":             50000,  # Artificially high
    "avg_balance":             80000,  # Inflated
    "balance_variance":        10000,
    "transaction_count":       45,
    "avg_debit":               3500,
    "large_transaction_ratio": 0.1,
    "credit_debit_ratio":      2.0
}])

# Simulate a legitimate statement
legitimate = pd.DataFrame([{
    "round_number_ratio":      0.02,   # Almost no round numbers
    "salary_is_round":         0,      # Odd salary (TDS deducted)
    "salary_variance":         500,    # Varies month to month
    "min_balance":             450,    # Ran low once
    "avg_balance":             35000,  # Normal savings
    "balance_variance":        15000,  # Natural fluctuation
    "transaction_count":       42,
    "avg_debit":               2200,
    "large_transaction_ratio": 0.02,
    "credit_debit_ratio":      1.1
}])

# Get fraud probability (not just yes/no)
suspicious_prob = model.predict_proba(suspicious)[0][1]
legitimate_prob = model.predict_proba(legitimate)[0][1]

print(f"Suspicious statement fraud probability:  "
      f"{suspicious_prob*100:.1f}%")
print(f"Legitimate statement fraud probability:  "
      f"{legitimate_prob*100:.1f}%")
print()

if suspicious_prob > 0.5:
    print("✅ Model correctly identified suspicious statement as FRAUD")
if legitimate_prob < 0.5:
    print("✅ Model correctly identified legitimate statement as LEGITIMATE")

# =============================================
# STEP 7 — Save the Model
# =============================================

# Save model to file so we can use it in FastAPI later
with open("ml/fraud_model.pkl", "wb") as f:
    pickle.dump(model, f)

print()
print("✅ Model saved to ml/fraud_model.pkl")
print("   This file will be loaded by FastAPI backend")