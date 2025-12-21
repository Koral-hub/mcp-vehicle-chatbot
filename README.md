# Projekt: Chatbot do Analizy Danych Pojazdów (MCP + LangChain + PostgreSQL + Docker)

## Cel Projektu
Stworzenie mini projektu chatbota opartego na LangChain i GPT, który będzie generował wykresy i analizy zużycia energii pojazdów na podstawie danych z bazy PostgreSQL, a wszystko to uruchomione w środowisku Docker.

## Architektura
*   **Orkiestracja LLM:** LangChain
*   **Model LLM:** GPT (przez API)
*   **Baza Danych:** PostgreSQL
*   **Konteneryzacja:** Docker
*   **Protokół:** Model Context Protocol (MCP)

## Struktura Danych (Tabela `vehicle_data`)

| Kolumna | Typ Danych | Opis |
| :--- | :--- | :--- |
| `id` | `SERIAL PRIMARY KEY` | Unikalny identyfikator rekordu. |
| `vehicle_id` | `VARCHAR(50)` | Identyfikator pojazdu (np. "PojazdXYZ"). |
| `timestamp` | `TIMESTAMP` | Czas pomiaru (kluczowe dla wykresów i obliczeń). |
| `speed_kmh` | `NUMERIC` | Prędkość pojazdu w km/h. |
| `traction_power_kw` | `NUMERIC` | Moc trakcyjna w kW. |
| `hvac_power_kw` | `NUMERIC` | Moc HVAC (ogrzewanie/klimatyzacja) w kW. |
| `distance_km` | `NUMERIC` | Dystans przejechany od ostatniego pomiaru w km. |

## Lista Narzędzi (Tools) dla Chatbota

1.  `fetch_data_for_chart`: Pobiera surowe dane (prędkość, moce) z bazy dla danego pojazdu i zakresu dat.
2.  `calculate_average_speed`: Oblicza średnią prędkość w danym okresie.
3.  `calculate_traction_energy_per_km`: Oblicza zużycie energii trakcyjnej w kWh/km.
4.  `calculate_hvac_energy_per_km`: Oblicza zużycie energii HVAC w kWh/km.
5.  `calculate_total_energy_per_km`: Oblicza całkowite zużycie energii w kWh/km.
6.  `calculate_total_distance`: Oblicza całkowity przejechany dystans.
7.  `generate_single_chart`: Generuje wykres dla pojedynczego parametru (np. tylko prędkość).
8.  `generate_multi_chart`: Generuje wykres dla wielu parametrów jednocześnie.
9.  `get_available_vehicles`: Zwraca listę dostępnych identyfikatorów pojazdów.
10. `format_analysis_report`: Formatuje wyniki obliczeń w czytelny raport tekstowy.

## Fazy Realizacji Projektu

1.  **Przygotowanie struktury projektu i dokumentacji planowania** (Zakończono)
2.  **Konfiguracja środowiska Docker** (PostgreSQL + Python/LangChain)
3.  **Utworzenie schematu bazy danych i generacja sztucznego datasetu**
4.  **Implementacja narzędzi (tools) do pobierania danych i obliczeń**
5.  **Implementacja narzędzi do generowania wykresów**
6.  **Budowa chatbota z integracją LangChain i GPT API**
7.  **Testowanie chatbota z przykładowymi zapytaniami**
8.  **Przygotowanie dokumentacji projektu i prezentacja wyników**
