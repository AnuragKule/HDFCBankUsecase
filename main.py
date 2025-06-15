from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import json
import os

app = FastAPI()
DATA_FILE = "transactions.json"

# ----- Pydantic model -----
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

# ----- File Helpers -----
def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ----- ID Generators -----
def generate_transaction_id(data):
    last_id = 0
    for item in data:
        num = int(item["Transaction_ID"].replace("TXN", ""))
        last_id = max(last_id, num)
    return f"TXN{last_id + 1:05d}"

def generate_customer_id(data):
    last_id = 1000
    for item in data:
        num = int(item["Customer_ID"].replace("CUST", ""))
        last_id = max(last_id, num)
    return f"CUST{last_id + 1}"

# ----- Add Transaction -----
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

# ----- Get Transactions by Phone -----
@app.get("/transactions/{phone_number}", response_model=List[TransactionOut])
def get_transactions(phone_number: str):
    data = load_data()
    txns = [t for t in data if t["Phone_Number"] == phone_number]
    if not txns:
        raise HTTPException(status_code=404, detail="No transactions found.")
    return txns

# ----- Update Transaction -----
@app.put("/update_transaction/{phone_number}/{txn_id}", response_model=TransactionOut)
def update_transaction(phone_number: str, txn_id: str, tx: TransactionIn):
    data = load_data()
    for i, item in enumerate(data):
        if item["Phone_Number"] == phone_number and item["Transaction_ID"] == txn_id:
            updated = tx.dict()
            updated["Transaction_ID"] = txn_id
            updated["Customer_ID"] = item["Customer_ID"]
            data[i] = updated
            save_data(data)
            return updated
    raise HTTPException(status_code=404, detail="Transaction not found.")

# ----- Delete Transaction -----
@app.delete("/delete_transaction/{phone_number}/{txn_id}")
def delete_transaction(phone_number: str, txn_id: str):
    data = load_data()
    new_data = [t for t in data if not (t["Phone_Number"] == phone_number and t["Transaction_ID"] == txn_id)]
    if len(new_data) == len(data):
        raise HTTPException(status_code=404, detail="Transaction not found.")
    save_data(new_data)
    return {"message": f"Transaction {txn_id} deleted successfully."}
