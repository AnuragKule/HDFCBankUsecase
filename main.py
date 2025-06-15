from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import json
import os

app = FastAPI()

# ✅ Use this file instead of transactions.json
DATA_FILE = "hdfc_transactions_with_phone.json"

# ----- Pydantic Models -----
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

# ----- Helper Functions -----
def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)

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

# ----- API Routes -----

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
@app.get("/transactions/{phone_number}", response_model=List[TransactionOut])
def get_transactions(phone_number: str):
    try:
        data = load_data()
        print("Loaded data count:", len(data))
        print("Searching for phone number:", phone_number)

        # Print keys from first record to validate
        if data:
            print("Available keys:", list(data[0].keys()))

        txns = [t for t in data if t.get("Phone_Number") == phone_number]

        print("Found transactions:", len(txns))
        if not txns:
            raise HTTPException(status_code=404, detail="No transactions found.")

        return txns

    except Exception as e:
        print("❌ Internal Error:", str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")

# ✅ Update a specific transaction
@app.put("/update_transaction/{phone_number}/{txn_id}", response_model=TransactionOut)
def update_transaction(phone_number: str, txn_id: str, tx: TransactionIn):
    data = load_data()

    for i, item in enumerate(data):
        if item.get("Phone_Number") == phone_number and item.get("Transaction_ID") == txn_id:
            updated_tx = tx.dict()
            updated_tx["Transaction_ID"] = txn_id  # Keep same
            updated_tx["Customer_ID"] = item["Customer_ID"]  # Keep same

            data[i] = updated_tx
            save_data(data)
            return updated_tx

    raise HTTPException(status_code=404, detail="Transaction not found.")



# ✅ Delete a transaction
@app.delete("/delete_transaction/{phone_number}/{txn_id}")
def delete_transaction(phone_number: str, txn_id: str):
    data = load_data()
    transaction_found = False

    # Filter out the transaction to be deleted
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
