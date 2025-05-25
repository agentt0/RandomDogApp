from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import requests
import random

app = FastAPI()

# CORS – żeby frontend (np. tkinter) mógł łączyć się z backendem
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DOG_API_URL = "https://api.thedogapi.com/v1"
API_KEY = "live_ztB47zHOn7uqStmgfpU9zEviOIvpmzh49o4uGa8ODYFAuORxBOtz5rupX3fXbhGZ"

HEADERS = {"x-api-key": API_KEY}


@app.get("/dog")
def get_random_dog(breed: str = Query(None)):
    if breed:
        # Znajdź ID rasy
        breeds = requests.get(f"{DOG_API_URL}/breeds", headers=HEADERS).json()
        breed_match = next((b for b in breeds if b["name"].lower() == breed.lower()), None)
        if not breed_match:
            return {"error": "Nie znaleziono rasy"}
        breed_id = breed_match["id"]

        # Pobierz losowego psa danej rasy
        params = {"breed_id": breed_id}
    else:
        # Pobierz losowego psa dowolnej rasy
        params = {}

    res = requests.get(f"{DOG_API_URL}/images/search", headers=HEADERS, params=params)
    data = res.json()[0]
    image_url = data["url"]
    breed_name = data["breeds"][0]["name"] if data.get("breeds") else "Nieznana rasa"

    return {
        "image_url": image_url,
        "breed": breed_name
    }


@app.get("/breeds")
def get_breeds():
    res = requests.get(f"{DOG_API_URL}/breeds", headers=HEADERS)
    data = res.json()
    breed_names = sorted([b["name"] for b in data])
    return breed_names
