import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import requests
from io import BytesIO
import json
import os
import subprocess
import time
import socket

# uruchamiamy serwer bezposrednio w aplikacji aby nie robic tego recznie przez terminal
# sprawdza czy serwer juz dziala
def is_server_running():
    try:
        with socket.create_connection(("127.0.0.1", 8000), timeout=1):
            return True
    except Exception:
        return False

# jesli serwer nie dziala, jest uruchamiany przez uvicorn
if not is_server_running():
    subprocess.Popen(
        ["uvicorn", "server:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(2)  # czas na uruchomienie serwera

# adres lokalnego API
API_URL = "http://127.0.0.1:8000"

# zmienne globalne do przechowywania biezacego obrazu i listy ulubionych
CURRENT_IMAGE = None
CURRENT_IMAGE_URL = None
FAVORITES = []
FAV_FILE = "favorites.json"

# funkcja wczytujaca ulubione z pliku json
def load_favorites():
    if os.path.exists(FAV_FILE):
        with open(FAV_FILE, "r") as f:
            return json.load(f)
    return []

# funkcja zapisujaca ulubione do pliku json
def save_favorites():
    with open(FAV_FILE, "w") as f:
        json.dump(FAVORITES, f, indent=2)

# glowna klasa aplikacji
class DogApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RandomDog") # nazwa aplikacji
        self.root.iconbitmap("dog_icon.ico")  # ustawienie ikony aplikacji
        self.root.geometry("600x700") # wielkosc okna aplikacji
        self.root.configure(bg="#fefefe")  # kolor tła

        style = ttk.Style()
        style.theme_use('clam')  # styl przyciskow

        # stworzenie dwoch zakladek: "Losuj psa" i "Ulubione", aby wszystko nie bylo w jednym oknie
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True)

        self.main_frame = tk.Frame(self.notebook, bg="#fefefe")
        self.fav_frame = tk.Frame(self.notebook, bg="#fefefe")
        self.notebook.add(self.main_frame, text="Losuj psa")
        self.notebook.add(self.fav_frame, text="Ulubione")

        self.main_tab()
        self.fav_tab()

        # wczytanie ulubionych i zaktualizowanie widoku
        global FAVORITES
        FAVORITES = load_favorites()
        self.update_fav_tab()

    # budowanie glownej zakladki - "Losuj psa"
    def main_tab(self):
        self.label = tk.Label(self.main_frame, text="Wybierz rasę lub wylosuj psa", font=("Verdana", 14, "bold"), bg="#fefefe")
        self.label.pack(pady=10)

        self.breed_combobox = ttk.Combobox(self.main_frame, state="readonly", width=40)
        self.breed_combobox.pack(pady=5)
        self.load_breeds()  # ladowanie listy ras

        self.button = ttk.Button(self.main_frame, text="Pokaż psa", command=self.fetch_dog)
        self.button.pack(pady=10) # przycisk "Pokaz psa"

        self.image_label = tk.Label(self.main_frame, bg="#fefefe")
        self.image_label.pack(pady=10)

        self.breed_label = tk.Label(self.main_frame, font=("Verdana", 12, "italic"), bg="#fefefe", fg="#555")
        self.breed_label.pack(pady=5)

        self.like_button = ttk.Button(self.main_frame, text="Dodaj do ulubionych", command=self.add_to_favorites)
        self.like_button.pack(pady=5) # przycisk "Dodaj do ulubionych"

        self.save_button = ttk.Button(self.main_frame, text="Zapisz zdjęcie", command=self.save_image)
        self.save_button.pack(pady=5) # przycisk "Zapisz zdjecie"

        self.loading_label = tk.Label(self.main_frame, text="", font=("Verdana", 10), bg="#fefefe", fg="#999")
        self.loading_label.pack()

    # budowanie zakładki - "Ulubione"
    def fav_tab(self):
        self.fav_canvas = tk.Canvas(self.fav_frame, bg="#fefefe")
        self.fav_scroll = ttk.Scrollbar(self.fav_frame, orient="vertical", command=self.fav_canvas.yview)
        self.scrollable_frame = tk.Frame(self.fav_canvas, bg="#fefefe")

        # aktualizacja scrollbara
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.fav_canvas.configure(scrollregion=self.fav_canvas.bbox("all"))
        )

        self.fav_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.fav_canvas.configure(yscrollcommand=self.fav_scroll.set)

        self.fav_canvas.pack(side="left", fill="both", expand=True)
        self.fav_scroll.pack(side="right", fill="y")

    # aktualizacja zawartosci zakladki ulubionych
    def update_fav_tab(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        for fav in FAVORITES:
            frame = tk.Frame(self.scrollable_frame, bg="#fefefe", bd=1, relief="solid")
            frame.pack(pady=10, padx=10, fill="x")

            try:
                img_data = requests.get(fav["url"]).content
                image = Image.open(BytesIO(img_data)).resize((200, 150))
                photo = ImageTk.PhotoImage(image)

                img_label = tk.Label(frame, image=photo, bg="#fefefe")
                img_label.image = photo
                img_label.pack(pady=5)

                # wyswietla nazwe rasy zapisanego psa
                breed_label = tk.Label(frame, text=f"Rasa: {fav['breed']}", font=("Verdana", 10), bg="#fefefe", fg="#333")
                breed_label.pack()

                btn_frame = tk.Frame(frame, bg="#fefefe")
                btn_frame.pack(pady=5)

                save_btn = ttk.Button(btn_frame, text="Zapisz", command=lambda url=fav["url"]: self.save_image_by_url(url))
                save_btn.pack(side="left", padx=5) # przycisk "Zapisz" do zapisywania zdjecia

                del_btn = ttk.Button(btn_frame, text="Usuń", command=lambda url=fav["url"]: self.remove_favorite(url))
                del_btn.pack(side="left", padx=5) # przycisk "Usuń"

            except Exception as e:
                error_label = tk.Label(frame, text=f"Błąd wczytania: {e}", bg="#fefefe", fg="red")
                error_label.pack()

    # wczytywanie dostepnych ras psow z API
    def load_breeds(self):
        try:
            res = requests.get(f"{API_URL}/breeds")
            breeds = res.json()
            self.breed_combobox["values"] = ["Losowy"] + breeds
            self.breed_combobox.set("Losowy")
        except Exception as e:
            self.label.config(text=f"Błąd ładowania ras: {e}")

    # pobieranie zdjecia psa
    def fetch_dog(self):
        global CURRENT_IMAGE, CURRENT_IMAGE_URL

        try:
            self.loading_label.config(text="Ładowanie...")
            self.root.update()

            # mozna wylosowac max 5 razy nowe zdjecie psa z konkretnej rasy
            breed = self.breed_combobox.get()
            attempts = 0
            max_attempts = 5
            new_img_url = CURRENT_IMAGE_URL

            # losowanie nowego zdjecia
            while new_img_url == CURRENT_IMAGE_URL and attempts < max_attempts:
                if breed == "Losowy":
                    res = requests.get(f"{API_URL}/dog")
                else:
                    res = requests.get(f"{API_URL}/dog", params={"breed": breed})
                data = res.json()

                new_img_url = data["image_url"]
                new_breed = data["breed"]
                attempts += 1

            if new_img_url == CURRENT_IMAGE_URL:
                self.loading_label.config(text="Nie znaleziono nowego zdjęcia. Spróbuj ponownie.")
                return

            img_data = requests.get(new_img_url).content
            image = Image.open(BytesIO(img_data)).resize((450, 350))
            photo = ImageTk.PhotoImage(image)

            self.image_label.config(image=photo)
            self.image_label.image = photo
            self.breed_label.config(text=f"Rasa: {new_breed}")
            self.loading_label.config(text="")

            CURRENT_IMAGE = image
            CURRENT_IMAGE_URL = new_img_url

        except Exception as e:
            self.label.config(text=f"Błąd: {e}")
            self.loading_label.config(text="")

    # dodanie obecnego psa do ulubionych
    def add_to_favorites(self):
        # blad jesli nie mamy wylosowanego psa a chcemy uzyc przycisku dodawania do ulubionych
        if not CURRENT_IMAGE_URL:
            self.loading_label.config(text="Najpierw wylosuj psa!")
            return

        # blad jesli chcemy ponownie zapisac zdjecie ktore juz znajduje sie w ulubionych
        if CURRENT_IMAGE_URL:
            for fav in FAVORITES:
                if fav["url"] == CURRENT_IMAGE_URL:
                    self.loading_label.config(text="To zdjęcie już jest w ulubionych.")
                    return
            breed = self.breed_label.cget("text").replace("Rasa: ", "")
            FAVORITES.append({"url": CURRENT_IMAGE_URL, "breed": breed}) # dodanie do listy ulubionych zdjecia i rasy
            save_favorites()
            self.update_fav_tab()
            self.loading_label.config(text="Dodano do ulubionych!")

    # zapisywanie zdjecia aktualnie wyswietlanego psa do nas na komputer
    def save_image(self):
        if CURRENT_IMAGE:
            file_path = filedialog.asksaveasfilename(defaultextension=".jpg", filetypes=[("JPEG", "*.jpg")])
            if file_path:
                CURRENT_IMAGE.save(file_path)
        else:
            self.loading_label.config(text="Najpierw wylosuj psa!") # blad jesli nie mamy wylosowanego zdjecia psa

    # zapis zdjecia psa na podstawie url (zapis z "Ulubionych" bo tam sa one zapisane w URL)
    def save_image_by_url(self, url):
        try:
            img_data = requests.get(url).content
            image = Image.open(BytesIO(img_data))
            file_path = filedialog.asksaveasfilename(defaultextension=".jpg", filetypes=[("JPEG", "*.jpg")])
            if file_path:
                image.save(file_path)
        except Exception as e:
            print(f"Błąd zapisu: {e}")

    # usuniecie psa z ulubionych
    def remove_favorite(self, url):
        global FAVORITES
        FAVORITES = [f for f in FAVORITES if f["url"] != url]
        save_favorites()
        self.update_fav_tab()

# uruchomienie aplikacji
if __name__ == "__main__":
    root = tk.Tk()
    app = DogApp(root)
    root.mainloop()
