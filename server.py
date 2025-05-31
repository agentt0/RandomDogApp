from fastapi import FastAPI, Query
import requests

app = FastAPI() # tworzymy fastapi

DOG_API_URL = "https://api.thedogapi.com/v1"  # adres "TheDogApi"
API_KEY = "live_ztB47zHOn7uqStmgfpU9zEviOIvpmzh49o4uGa8ODYFAuORxBOtz5rupX3fXbhGZ"  # klucz autoryzacyjny

HEADERS = {"x-api-key": API_KEY}

# endpoint /dog - zwracajacy losowego psa lub konkretnej rasy
@app.get("/dog")
def get_random_dog(breed: str = Query(None)):
    if breed:
        # jesli podano nazwe rasy, pobranie listy ras i znalezienie odpowiadajaca nazwe
        breeds = requests.get(f"{DOG_API_URL}/breeds", headers=HEADERS).json()
        breed_match = next((b for b in breeds if b["name"].lower() == breed.lower()), None)
        if not breed_match:
            return {"error": "nie znaleziono rasy"}  # blad gdy rasa nie zostala znaleziona
        breed_id = breed_match["id"]  # wyciaga id rasy
        params = {"breed_id": breed_id}  # dodaje parametr do zapytania o konkretnej rasie
    else:
        # jesli nie podano rasy, nie ustawiaj parametru
        params = {}

    # pobiera losowy obrazek psa (z opcjonalnym filtrem rasy)
    res = requests.get(f"{DOG_API_URL}/images/search", headers=HEADERS, params=params)
    data = res.json()[0]  # bierze pierwszy wynik z listy
    image_url = data["url"]  # url do obrazka psa
    breed_name = data["breeds"][0]["name"] if data.get("breeds") else "nieznana rasa"  # nazwa rasy (jesli jest)

    return {
        "image_url": image_url,
        "breed": breed_name
    }

# endpoint /breeds - zwracajacy posortowana alfabetycznie liste wszystkich ras
@app.get("/breeds")
def get_breeds():
    res = requests.get(f"{DOG_API_URL}/breeds", headers=HEADERS)  # zapytanie o liste ras
    data = res.json()  # zmiana odpowiedzi na plik json
    breed_names = sorted([b["name"] for b in data])  # sortowanie nazw ras
    return breed_names
