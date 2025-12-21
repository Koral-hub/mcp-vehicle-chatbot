import os
import psycopg2
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
import plotly.express as px
import plotly.io as pio
import json
from langchain.tools import tool

# Ustawienie renderera Plotly na 'json' do zwracania wykresów jako JSON
# W normalnym środowisku użyłbym 'png' lub 'jpeg', ale w tym przypadku JSON jest bezpieczniejszy
# do przekazania przez narzędzie.
pio.templates.default = "plotly_white"

# Wczytanie zmiennych środowiskowych
load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    """Ustanawia połączenie z bazą danych PostgreSQL."""
    if not DB_URL:
        raise ValueError("DATABASE_URL nie jest ustawione w zmiennych środowiskowych.")
    return psycopg2.connect(DB_URL)

@tool
def get_available_vehicles() -> List[str]:
    """
    Zwraca listę unikalnych identyfikatorów pojazdów dostępnych w bazie danych.
    
    :return: Lista identyfikatorów pojazdów (np. ['Pojazd_1', 'Pojazd_2']).
    """
    conn = None
    try:
        conn = get_db_connection()
        query = "SELECT DISTINCT vehicle_id FROM vehicle_data ORDER BY vehicle_id;"
        df = pd.read_sql(query, conn)
        return df['vehicle_id'].tolist()
    except Exception as e:
        return [f"Błąd podczas pobierania listy pojazdów: {e}"]
    finally:
        if conn:
            conn.close()

@tool
def get_data_range(vehicle_id: str) -> str:
    """
    Zwraca minimalną i maksymalną datę (zakres) dostępnych danych dla danego pojazdu.
    
    :param vehicle_id: Identyfikator pojazdu (np. 'Pojazd_1').
    :return: String z zakresem dat (np. '2025-02-10 do 2025-02-14').
    """
    conn = None
    try:
        conn = get_db_connection()
        query = f"""
        SELECT MIN(timestamp) as min_date, MAX(timestamp) as max_date
        FROM vehicle_data
        WHERE vehicle_id = %s;
        """
        df = pd.read_sql(query, conn, params=(vehicle_id,))
        
        min_date = df['min_date'].iloc[0].strftime('%Y-%m-%d')
        max_date = df['max_date'].iloc[0].strftime('%Y-%m-%d')
        
        return f"Zakres dat dla {vehicle_id}: od {min_date} do {max_date}."
    except Exception as e:
        return f"Błąd podczas pobierania zakresu dat: {e}"
    finally:
        if conn:
            conn.close()


@tool
def fetch_data_for_chart(vehicle_id: str, start_date: str, end_date: str) -> str:
    """
    Pobiera surowe dane telemetryczne (prędkość, moce, dystans) dla danego pojazdu 
    w określonym zakresie dat. Dane są zwracane jako string w formacie JSON, 
    gotowe do użycia przez narzędzia do generowania wykresów.

    :param vehicle_id: Identyfikator pojazdu (np. 'Pojazd_1').
    :param start_date: Data początkowa w formacie 'YYYY-MM-DD' (np. '2025-02-13').
    :param end_date: Data końcowa w formacie 'YYYY-MM-DD' (np. '2025-02-15').
    :return: String JSON z danymi lub komunikat o błędzie/braku danych.
    """
    conn = None
    try:
        conn = get_db_connection()
        query = f"""
        SELECT timestamp, speed_kmh, traction_power_kw, hvac_power_kw, distance_km
        FROM vehicle_data
        WHERE vehicle_id = %s AND timestamp >= %s AND timestamp < %s
        ORDER BY timestamp;
        """
        # Dodajemy jeden dzień do end_date, aby uwzględnić cały dzień końcowy
        end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        
        df = pd.read_sql(query, conn, params=(vehicle_id, start_date, end_dt.strftime('%Y-%m-%d')))
        
        if df.empty:
            return f"Brak danych dla pojazdu {vehicle_id} w zakresie od {start_date} do {end_date}."
        
        # Konwersja timestamp na string dla łatwiejszego przekazania w JSON
        df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Zwracamy dane jako string JSON
        return df.to_json(orient='records')
    except Exception as e:
        return f"Błąd podczas pobierania danych: {e}"
    finally:
        if conn:
            conn.close()

def _calculate_energy_consumption(df: pd.DataFrame, power_col: str) -> float:
    """Wewnętrzna funkcja do obliczania zużycia energii w kWh/km."""
    if df.empty:
        return 0.0
    
    # Czas między pomiarami to 1 minuta (1/60 godziny)
    time_interval_h = 1/60 
    
    # Energia w kWh = Moc w kW * Czas w h
    df['energy_kwh'] = df[power_col] * time_interval_h
    
    total_energy_kwh = df['energy_kwh'].sum()
    total_distance_km = df['distance_km'].sum()
    
    if total_distance_km == 0:
        return 0.0
        
    # Zużycie w kWh/km
    consumption = total_energy_kwh / total_distance_km
    return round(consumption, 4)

@tool
def calculate_average_speed(data_json: str) -> float:
    """
    Oblicza średnią prędkość (km/h) na podstawie danych telemetrycznych.

    :param data_json: String JSON z danymi zwrócony przez fetch_data_for_chart.
    :return: Średnia prędkość w km/h.
    """
    try:
        df = pd.read_json(data_json)
        if df.empty:
            return 0.0
        return round(df['speed_kmh'].mean(), 2)
    except Exception:
        return 0.0
    
@tool
def calculate_total_distance(data_json: str) -> float:
    """
    Oblicza całkowity przejechany dystans (km) na podstawie danych telemetrycznych.

    :param data_json: String JSON z danymi zwrócony przez fetch_data_for_chart.
    :return: Całkowity dystans w km.
    """
    try:
        df = pd.read_json(data_json)
        if df.empty:
            return 0.0
        return round(df['distance_km'].sum(), 2)
    except Exception:
        return 0.0
    
@tool
def calculate_traction_energy_per_km(data_json: str) -> float:
    """
    Oblicza zużycie energii trakcyjnej w kWh/km.

    :param data_json: String JSON z danymi zwrócony przez fetch_data_for_chart.
    :return: Zużycie energii trakcyjnej w kWh/km.
    """
    try:
        df = pd.read_json(data_json)
        return _calculate_energy_consumption(df, 'traction_power_kw')
    except Exception:
        return 0.0
    
@tool
def calculate_hvac_energy_per_km(data_json: str) -> float:
    """
    Oblicza zużycie energii HVAC w kWh/km.

    :param data_json: String JSON z danymi zwrócony przez fetch_data_for_chart.
    :return: Zużycie energii HVAC w kWh/km.
    """
    try:
        df = pd.read_json(data_json)
        return _calculate_energy_consumption(df, 'hvac_power_kw')
    except Exception:
        return 0.0
    
@tool
def calculate_total_energy_per_km(data_json: str) -> float:
    """
    Oblicza całkowite zużycie energii (trakcja + HVAC) w kWh/km.

    :param data_json: String JSON z danymi zwrócony przez fetch_data_for_chart.
    :return: Całkowite zużycie energii w kWh/km.
    """
    try:
        df = pd.read_json(data_json)
        # Tworzenie kolumny z sumą mocy
        df['total_power_kw'] = df['traction_power_kw'] + df['hvac_power_kw']
        return _calculate_energy_consumption(df, 'total_power_kw')
    except Exception:
        return 0.0

@tool
def format_analysis_report(vehicle_id: str, start_date: str, end_date: str, data_json: str) -> str:
    """
    Generuje czytelny raport tekstowy podsumowujący analizę danych.
    Wykorzystuje inne narzędzia do obliczeń i formatuje wyniki.

    :param vehicle_id: Identyfikator pojazdu.
    :param start_date: Data początkowa.
    :param end_date: Data końcowa.
    :param data_json: String JSON z danymi zwrócony przez fetch_data_for_chart.
    :return: Sformatowany raport tekstowy.
    """
    avg_speed = calculate_average_speed(data_json)
    total_dist = calculate_total_distance(data_json)
    traction_cons = calculate_traction_energy_per_km(data_json)
    hvac_cons = calculate_hvac_energy_per_km(data_json)
    total_cons = calculate_total_energy_per_km(data_json)
    
    report = f"""
    --- RAPORT ANALIZY DANYCH POJAZDU ---
    Pojazd: {vehicle_id}
    Okres: od {start_date} do {end_date}
    
    PODSUMOWANIE:
    - Całkowity przejechany dystans: {total_dist} km
    - Średnia prędkość w okresie: {avg_speed} km/h
    
    ZUŻYCIE ENERGII (kWh/km):
    - Trakcja: {traction_cons} kWh/km
    - HVAC: {hvac_cons} kWh/km
    - Całkowite: {total_cons} kWh/km
    
    --- KONIEC RAPORTU ---
    """
    return report.strip()

@tool
def generate_single_chart(data_json: str, parameter: str) -> str:
    """
    Generuje wykres liniowy dla pojedynczego parametru (np. 'speed_kmh').

    :param data_json: String JSON z danymi zwrócony przez fetch_data_for_chart.
    :param parameter: Nazwa kolumny do wykreślenia (np. 'speed_kmh', 'traction_power_kw').
    :return: String JSON z definicją wykresu Plotly.
    """
    try:
        df = pd.read_json(data_json)
        if df.empty:
            return json.dumps({"error": "Brak danych do wygenerowania wykresu."})
        
        # Konwersja timestamp z powrotem na datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        title_map = {
            'speed_kmh': 'Prędkość (km/h)',
            'traction_power_kw': 'Moc Trakcyjna (kW)',
            'hvac_power_kw': 'Moc HVAC (kW)',
            'distance_km': 'Dystans (km)'
        }
        
        fig = px.line(df, x='timestamp', y=parameter, 
                      title=f'Wykres {title_map.get(parameter, parameter)} w czasie',
                      labels={'timestamp': 'Czas', parameter: title_map.get(parameter, parameter)})
        
        return fig.to_json()
    except Exception as e:
        return json.dumps({"error": f"Błąd podczas generowania wykresu dla {parameter}: {e}"})
    
@tool
def generate_multi_chart(data_json: str, parameters: List[str]) -> str:
    """
    Generuje wykres liniowy dla wielu parametrów na jednym wykresie.

    :param data_json: String JSON z danymi zwrócony przez fetch_data_for_chart.
    :param parameters: Lista nazw kolumn do wykreślenia (np. ['speed_kmh', 'traction_power_kw']).
    :return: String JSON z definicją wykresu Plotly.
    """
    try:
        df = pd.read_json(data_json)
        if df.empty:
            return json.dumps({"error": "Brak danych do wygenerowania wykresu."})
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Plotly Express automatycznie obsługuje wiele serii danych
        fig = px.line(df, x='timestamp', y=parameters, 
                      title='Wykres wielu parametrów telemetrycznych w czasie',
                      labels={'timestamp': 'Czas', 'value': 'Wartość', 'variable': 'Parametr'})
        
        return fig.to_json()
    except Exception as e:
        return json.dumps({"error": f"Błąd podczas generowania wykresu dla wielu parametrów: {e}"})

# Jeśli chcesz przetestować toolsy lokalnie (po uruchomieniu Dockera):
if __name__ == "__main__":
    print("Dostępne pojazdy:", get_available_vehicles())
    
    # Przykładowe użycie fetch_data_for_chart
    vehicle = "Pojazd_1"
    start = "2025-02-13"
    end = "2025-02-15"
    
    data = fetch_data_for_chart(vehicle, start, end)
    
    if data.startswith("Błąd") or data.startswith("Brak"):
        print(data)
    else:
        print(f"\nPobrano dane dla {vehicle}. Liczba rekordów: {len(pd.read_json(data))}")
        
        # Przykładowe użycie narzędzi analitycznych
        print("\n--- Analiza Danych ---")
        print(f"Średnia prędkość: {calculate_average_speed(data)} km/h")
        print(f"Całkowity dystans: {calculate_total_distance(data)} km")
        print(f"Zużycie trakcji: {calculate_traction_energy_per_km(data)} kWh/km")
        print(f"Zużycie HVAC: {calculate_hvac_energy_per_km(data)} kWh/km")
        print(f"Całkowite zużycie: {calculate_total_energy_per_km(data)} kWh/km")
        
        # Generowanie raportu
        report = format_analysis_report(vehicle, start, end, data)
        print(report)
        
        # Generowanie wykresu (zwraca JSON)
        chart_json = generate_single_chart(data, 'speed_kmh')
        print("\n--- Wykres Prędkości (JSON Plotly) ---")
        # print(chart_json[:200] + "...") # Drukujemy tylko fragment
        
        multi_chart_json = generate_multi_chart(data, ['speed_kmh', 'traction_power_kw'])
        print("\n--- Wykres Multi (JSON Plotly) ---")
        # print(multi_chart_json[:200] + "...") # Drukujemy tylko fragment
