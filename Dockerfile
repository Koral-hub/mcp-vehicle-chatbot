# Użycie oficjalnego obrazu Pythona
FROM python:3.11-slim

# Instalacja zależności systemowych wymaganych przez psycopg2-binary
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Ustawienie katalogu roboczego
WORKDIR /app

# Kopiowanie pliku z zależnościami i instalacja
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiowanie reszty plików projektu
COPY . .

# Komenda uruchamiająca aplikację (może być zmieniona później)
CMD ["tail", "-f", "/dev/null"]
