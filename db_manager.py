import os
import psycopg2
from dotenv import load_dotenv
from faker import Faker
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Wczytanie zmiennych środowiskowych z pliku .env
load_dotenv()

# Konfiguracja połączenia z bazą danych
DB_URL = os.getenv("DATABASE_URL")

# Struktura tabeli
CREATE_TABLE_QUERY = """
CREATE TABLE IF NOT EXISTS vehicle_data (
    id SERIAL PRIMARY KEY,
    vehicle_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    speed_kmh NUMERIC,
    traction_power_kw NUMERIC,
    hvac_power_kw NUMERIC,
    distance_km NUMERIC
);
"""

def create_table(conn):
    """Tworzy tabelę vehicle_data, jeśli nie istnieje."""
    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_QUERY)
            conn.commit()
        print("Tabela 'vehicle_data' została utworzona lub już istnieje.")
    except Exception as e:
        print(f"Błąd podczas tworzenia tabeli: {e}")
        raise

def generate_synthetic_data(num_records=1000, num_vehicles=3):
    """Generuje sztuczne dane telemetryczne pojazdów."""
    fake = Faker()
    data = []
    vehicle_ids = [f"Pojazd_{i+1}" for i in range(num_vehicles)]
    start_date = datetime(2025, 2, 10)
    
    for vehicle_id in vehicle_ids:
        current_time = start_date
        last_speed = 0
        
        for _ in range(num_records // num_vehicles):
            # Symulacja upływu czasu (np. co 1 minutę)
            current_time += timedelta(minutes=1)
            
            # Symulacja prędkości (zależna od poprzedniej, z szumem)
            speed_change = np.random.normal(loc=0, scale=5)
            new_speed = max(0, last_speed + speed_change)
            
            # Symulacja mocy trakcyjnej (zależna od prędkości)
            traction_power = max(0, new_speed * 0.5 + np.random.normal(loc=5, scale=10))
            
            # Symulacja mocy HVAC (stała + szum)
            hvac_power = max(0, 3 + np.random.normal(loc=0, scale=1))
            
            # Obliczenie dystansu (prędkość * czas w godzinach)
            # Czas między pomiarami to 1 minuta = 1/60 godziny
            distance_km = new_speed * (1/60)
            if distance_km == 0:
                distance_km = 0.000001 # Minimalny dystans, aby uniknąć błędu
            
            data.append({
                "vehicle_id": vehicle_id,
                "timestamp": current_time,
                "speed_kmh": round(new_speed, 2),
                "traction_power_kw": round(traction_power, 2),
                "hvac_power_kw": round(hvac_power, 2),
                "distance_km": round(distance_km, 4)
            })
            
            last_speed = new_speed

    df = pd.DataFrame(data)
    # Sortowanie danych chronologicznie
    df = df.sort_values(by=['vehicle_id', 'timestamp']).reset_index(drop=True)
    print(f"Wygenerowano {len(df)} rekordów danych.")
    return df

def insert_data(conn, df):
    """Wstawia dane z DataFrame do tabeli vehicle_data."""
    try:
        with conn.cursor() as cur:
            # Przygotowanie zapytania INSERT
            insert_query = """
            INSERT INTO vehicle_data (vehicle_id, timestamp, speed_kmh, traction_power_kw, hvac_power_kw, distance_km)
            VALUES (%s, %s, %s, %s, %s, %s);
            """
            
            # Iteracja i wstawianie danych
            for index, row in df.iterrows():
                cur.execute(insert_query, (
                    row['vehicle_id'],
                    row['timestamp'],
                    row['speed_kmh'],
                    row['traction_power_kw'],
                    row['hvac_power_kw'],
                    row['distance_km']
                ))
            
            conn.commit()
        print(f"Pomyślnie wstawiono {len(df)} rekordów do bazy danych.")
    except Exception as e:
        print(f"Błąd podczas wstawiania danych: {e}")
        raise

def setup_database():
    """Główna funkcja do konfiguracji bazy danych i wstawiania danych."""
    if not DB_URL:
        print("Błąd: Zmienna środowiskowa DATABASE_URL nie jest ustawiona.")
        print("Upewnij się, że plik .env jest poprawnie skonfigurowany.")
        return

    conn = None
    try:
        # Nawiązanie połączenia z bazą danych
        conn = psycopg2.connect(DB_URL)
        
        # 1. Tworzenie tabeli
        create_table(conn)
        
        # 2. Generowanie danych
        data_df = generate_synthetic_data(num_records=300, num_vehicles=3)
        
        # 3. Wstawianie danych
        insert_data(conn, data_df)
        
    except psycopg2.OperationalError as e:
        print("\n" + "="*50)
        print("BŁĄD POŁĄCZENIA Z BAZĄ DANYCH!")
        print("Upewnij się, że kontener PostgreSQL jest uruchomiony i dostępny pod adresem podanym w DATABASE_URL.")
        print(f"Szczegóły błędu: {e}")
        print("="*50 + "\n")
    except Exception as e:
        print(f"Wystąpił nieoczekiwany błąd: {e}")
    finally:
        if conn:
            conn.close()
            print("Połączenie z bazą danych zostało zamknięte.")

if __name__ == "__main__":
    setup_database()
