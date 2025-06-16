from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import json
import os

app = FastAPI()

# ✅ JSON file used for storing transactions
DATA_FILE = "hdfc_transactions_with_phone.json"

# ------------------- Models -------------------

class TransactionIn(BaseModel):
    Account_Number: str
    Transaction_Date: str
    Description: str
    Category: str
    Transaction_Amount: float
    Account_Balance: float
    Transaction_Type: str
    Mode: str
    Merchant_or_Payee: str
    IFSC_Code: str
    Location: str
    Phone_Number: str

class TransactionOut(TransactionIn):
    Transaction_ID: str
    Customer_ID: str

# ------------------- Helper Functions -------------------

def normalize_keys(record):
    return {
        "Account_Number": record.get("Account Number", record.get("Account_Number")),
        "Transaction_Date": record.get("Transaction Date", record.get("Transaction_Date")),
        "Description": record.get("Description"),
        "Category": record.get("Category"),
        "Transaction_Amount": record.get("Transaction Amount", record.get("Transaction_Amount")),
        "Account_Balance": record.get("Account Balance", record.get("Account_Balance")),
        "Transaction_Type": record.get("Transaction Type", record.get("Transaction_Type")),
        "Mode": record.get("Mode"),
        "Merchant_or_Payee": record.get("Merchant/Payee", record.get("Merchant_or_Payee")),
        "IFSC_Code": record.get("IFSC Code", record.get("IFSC_Code")),
        "Location": record.get("Location"),
        "Phone_Number": record.get("Phone Number", record.get("Phone_Number")),
        "Transaction_ID": record.get("Transaction ID", record.get("Transaction_ID")),
        "Customer_ID": record.get("Customer ID", record.get("Customer_ID")),
    }

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r") as f:
            raw_data = json.load(f)
            return [normalize_keys(record) for record in raw_data]
    except json.JSONDecodeError:
        print("❌ Error: Could not parse JSON.")
        return []

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def generate_transaction_id(data):
    last_id = 0
    for item in data:
        try:
            num = int(item["Transaction_ID"].replace("TXN", ""))
            last_id = max(last_id, num)
        except:
            continue
    return f"TXN{last_id + 1:05d}"

def generate_customer_id(data):
    last_id = 1000
    for item in data:
        try:
            num = int(item["Customer_ID"].replace("CUST", ""))
            last_id = max(last_id, num)
        except:
            continue
    return f"CUST{last_id + 1}"

# ------------------- API Routes -------------------

# ✅ Add a new transaction
@app.post("/add_transaction", response_model=TransactionOut)
def add_transaction(tx: TransactionIn):
    data = load_data()
    transaction_id = generate_transaction_id(data)
    customer_id = generate_customer_id(data)

    tx_data = tx.dict()
    tx_data["Transaction_ID"] = transaction_id
    tx_data["Customer_ID"] = customer_id

    data.append(tx_data)
    save_data(data)

    return tx_data

# ✅ Get all transactions by phone number
from fastapi import Query

@app.get("/transactions/search", response_model=List[TransactionOut])
def search_transactions(
    phone_number: str = Query(None),
    transaction_type: str = Query(None),
    category: str = Query(None),
    merchant: str = Query(None),
    mode: str = Query(None),
    location: str = Query(None)
):
    try:
        data = load_data()
        print(f"🔍 Searching by phone: {phone_number}, type: {transaction_type}, category: {category}, merchant: {merchant}, mode: {mode}, location: {location}")

        filtered = []

        for txn in data:
            if phone_number and txn.get("Phone_Number") != phone_number:
                continue
            if transaction_type and txn.get("Transaction_Type") != transaction_type:
                continue
            if category and category.lower() not in txn.get("Category", "").lower():
                continue
            if merchant and merchant.lower() not in txn.get("Merchant_or_Payee", "").lower():
                continue
            if mode and mode.lower() != txn.get("Mode", "").lower():
                continue
            if location and location.lower() not in txn.get("Location", "").lower():
                continue

            filtered.append(txn)

        if not filtered:
            raise HTTPException(status_code=404, detail="No transactions match the criteria.")

        return filtered

    except Exception as e:
        print("❌ Internal Error:", str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")

# ✅ Update a specific transaction
@app.put("/update_transaction/{phone_number}/{txn_id}", response_model=TransactionOut)
def update_transaction(phone_number: str, txn_id: str, tx: TransactionIn):
    data = load_data()

    for i, item in enumerate(data):
        normalized_item = normalize_keys(item)  # ✅ Normalize keys
        if normalized_item.get("Phone_Number") == phone_number and normalized_item.get("Transaction_ID") == txn_id:
            updated_tx = tx.dict()
            updated_tx["Transaction_ID"] = normalized_item["Transaction_ID"]
            updated_tx["Customer_ID"] = normalized_item["Customer_ID"]

            data[i] = updated_tx
            save_data(data)
            return updated_tx

    raise HTTPException(status_code=404, detail="Transaction not found.")

# ✅ Delete a transaction
@app.delete("/delete_transaction/{phone_number}/{txn_id}")
def delete_transaction(phone_number: str, txn_id: str):
    data = load_data()
    transaction_found = False

    new_data = []
    for txn in data:
        if txn.get("Phone_Number") == phone_number and txn.get("Transaction_ID") == txn_id:
            transaction_found = True
            continue
        new_data.append(txn)

    if not transaction_found:
        raise HTTPException(status_code=404, detail="Transaction not found.")

    save_data(new_data)
    return {"message": f"Transaction {txn_id} deleted successfully."}
