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
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir streamlit

# Kopiowanie reszty plików projektu
COPY . .

# Komenda uruchamiająca aplikację Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
