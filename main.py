from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import requests
import os
import pickle
import numpy as np

BASE = os.path.dirname(__file__)
DB = os.path.join(BASE, "krishicare.db")
MODEL = os.path.join(BASE, "krishicare_crop_model.pkl")

app = FastAPI(title="KrishiCare API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con=db()
    con.execute("""CREATE TABLE IF NOT EXISTS farmers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        location TEXT,
        crop TEXT
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS observations(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        farmer_id INTEGER,
        soil_moisture REAL,
        temperature REAL,
        note TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    con.commit(); con.close()

init_db()

class FarmerIn(BaseModel):
    name: str
    phone: str = ""
    location: str = ""
    crop: str = "Wheat"

class ObservationIn(BaseModel):
    farmer_id: int
    soil_moisture: float
    temperature: float
    note: str = ""

@app.get("/api/health")
def health():
    return {"status":"ok","message":"KrishiCare backend is running"}

@app.post("/api/farmers")
def create_farmer(data: FarmerIn):
    con=db()
    cur=con.execute("INSERT INTO farmers(name,phone,location,crop) VALUES(?,?,?,?)",
                    (data.name,data.phone,data.location,data.crop))
    con.commit()
    farmer_id=cur.lastrowid
    con.close()
    return {"id":farmer_id, **data.model_dump()}

@app.get("/api/farmers")
def list_farmers():
    con=db()
    rows=[dict(r) for r in con.execute("SELECT * FROM farmers ORDER BY id DESC").fetchall()]
    con.close()
    return rows

@app.post("/api/observations")
def add_observation(data: ObservationIn):
    con=db()
    exists=con.execute("SELECT id FROM farmers WHERE id=?",(data.farmer_id,)).fetchone()
    if not exists:
        con.close(); raise HTTPException(404,"Farmer not found")
    cur=con.execute("""INSERT INTO observations
        (farmer_id,soil_moisture,temperature,note) VALUES(?,?,?,?)""",
        (data.farmer_id,data.soil_moisture,data.temperature,data.note))
    con.commit(); con.close()
    return {"id":cur.lastrowid,"message":"Observation saved"}

@app.get("/api/observations/{farmer_id}")
def observations(farmer_id:int):
    con=db()
    rows=[dict(r) for r in con.execute(
        "SELECT * FROM observations WHERE farmer_id=? ORDER BY id DESC",(farmer_id,)
    ).fetchall()]
    con.close()
    return rows

@app.get("/api/weather")
def weather(latitude: float=28.61, longitude: float=77.23):
    # Open-Meteo does not require an API key for this prototype.
    url=("https://api.open-meteo.com/v1/forecast"
         f"?latitude={latitude}&longitude={longitude}"
         "&current=temperature_2m,relative_humidity_2m,precipitation"
         "&hourly=precipitation_probability&forecast_days=1")
    try:
        r=requests.get(url,timeout=8); r.raise_for_status()
        data=r.json()
        probs=data.get("hourly",{}).get("precipitation_probability",[])
        return {
            "temperature": data.get("current",{}).get("temperature_2m"),
            "humidity": data.get("current",{}).get("relative_humidity_2m"),
            "precipitation": data.get("current",{}).get("precipitation"),
            "rain_probability": max(probs[:6]) if probs else None
        }
    except Exception:
        return {"error":"Weather service unavailable. Showing safe demo fallback.",
                "temperature":31,"humidity":55,"precipitation":0,"rain_probability":20}

def load_model():
    if os.path.exists(MODEL):
        with open(MODEL,"rb") as f: return pickle.load(f)
    return None

@app.post("/api/ai/recommendation")
def recommendation(
    soil_moisture: float,
    temperature: float,
    rain_probability: float = 20,
    N: float = 50,
    P: float = 40,
    K: float = 40,
    humidity: float = 60,
    ph: float = 6.5,
    rainfall: float = 0
):
    model = load_model()

    prediction = "Model unavailable"

    if model:
        try:
            features = np.array([[
                N, P, K, temperature, humidity, ph, rainfall
            ]])

            prediction = model.predict(features)[0]

        except Exception as e:
            prediction = "Prediction error"

    if soil_moisture < 30 and rain_probability < 50:
        action = "Soil moisture is low. Check the field and consider irrigation based on crop needs."
    elif rain_probability >= 50:
        action = "Rain is likely soon. Check the field before irrigating."
    else:
        action = "Soil moisture looks reasonable. Continue monitoring the field."

    return {
        "prediction": str(prediction),
        "action": action,
        "inputs": {
            "N": N,
            "P": P,
            "K": K,
            "temperature": temperature,
            "humidity": humidity,
            "ph": ph,
            "rainfall": rainfall
        },
        "disclaimer": "Prototype recommendation; verify with a qualified local agricultural expert."
    }
