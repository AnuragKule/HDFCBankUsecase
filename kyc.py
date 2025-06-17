from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import json
import os

app = FastAPI()

# 🔸 Data file
DATA_FILE = "kyc_profiles.json"

# -------------------------------
# 🔸 Pydantic Models
# -------------------------------
class KYCProfileIn(BaseModel):
    PREFIX: str
    FNAME: str
    LNAME: str
    FULLNAME: Optional[str] = None
    GENDER: str
    DOB: str
    PAN: str
    Address: str
    PERM_PIN: str
    MOB_CODE: str
    MOB_NUM: str
    EMAIL_ID: str

class KYCProfileOut(KYCProfileIn):
    KYC_ID: str

# -------------------------------
# 🔸 Helper Functions
# -------------------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def generate_kyc_id(data):
    last_id = 0
    for item in data:
        try:
            num = int(item["KYC_ID"].replace("KYC", ""))
            last_id = max(last_id, num)
        except:
            continue
    return f"KYC{last_id + 1:04d}"

# -------------------------------
# 🔸 API Routes
# -------------------------------

@app.post("/add_profile", response_model=KYCProfileOut)
def add_profile(profile: KYCProfileIn):
    data = load_data()

    # Prevent duplicate PAN
    for existing in data:
        if existing["PAN"] == profile.PAN:
            raise HTTPException(status_code=400, detail="Profile with this PAN already exists.")

    profile_dict = profile.dict()

    # Set FULLNAME if not provided
    if not profile_dict.get("FULLNAME"):
        profile_dict["FULLNAME"] = f"{profile_dict['PREFIX']} {profile_dict['FNAME']} {profile_dict['LNAME']}"

    # Generate unique KYC_ID
    profile_dict["KYC_ID"] = generate_kyc_id(data)

    data.append(profile_dict)
    save_data(data)

    return profile_dict

@app.get("/profiles", response_model=List[KYCProfileOut])
def get_all_profiles():
    return load_data()

@app.get("/profile", response_model=List[KYCProfileOut])
def get_profile(
    phone: Optional[str] = Query(None), 
    dob: Optional[str] = Query(None), 
    pan: Optional[str] = Query(None)
):
    data = load_data()

    if phone and not pan and not dob:
        results = [p for p in data if p.get("MOB_NUM") == phone]

    elif pan and dob and not phone:
        results = [p for p in data if p.get("PAN") == pan and p.get("DOB") == dob]

    elif phone and pan and not dob:
        results = [p for p in data if p.get("PAN") == pan and p.get("MOB_NUM") == phone]

    else:
        results = []

    if not results:
        raise HTTPException(status_code=404, detail="Profile not found.")

    return results