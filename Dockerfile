# Użycie oficjalnego obrazu Pythona
FROM python:3.11-slim

# Ustawienie katalogu roboczego
WORKDIR /app

# Kopiowanie pliku z zależnościami i instalacja
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiowanie reszty plików projektu
COPY . .

# Komenda uruchamiająca aplikację (może być zmieniona później)
CMD ["python", "main.py"]
