import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage
from tools import (
    get_available_vehicles,
    fetch_data_for_chart,
    calculate_average_speed,
    calculate_total_distance,
    calculate_traction_energy_per_km,
    calculate_hvac_energy_per_km,
    calculate_total_energy_per_km,
    format_analysis_report,
    generate_single_chart,
    generate_multi_chart
)

# Wczytanie zmiennych środowiskowych
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY or OPENAI_API_KEY == "TWOJ_KLUCZ_API_GPT":
    print("BŁĄD: Uzupełnij klucz OPENAI_API_KEY w pliku .env!")
    exit()

# 1. Definicja narzędzi (Tools)
tools = [
    get_available_vehicles,
    fetch_data_for_chart,
    calculate_average_speed,
    calculate_total_distance,
    calculate_traction_energy_per_km,
    calculate_hvac_energy_per_km,
    calculate_total_energy_per_km,
    format_analysis_report,
    generate_single_chart,
    generate_multi_chart
]

# 2. Inicjalizacja modelu LLM
# Używamy modelu zdolnego do wywoływania narzędzi (tool calling)
llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0, api_key=OPENAI_API_KEY)

# 3. Definicja promptu systemowego
system_prompt = """
Jesteś zaawansowanym asystentem do analizy danych telemetrycznych pojazdów. 
Twoim zadaniem jest odpowiadanie na pytania użytkownika dotyczące prędkości, 
dystansu i zużycia energii pojazdów w określonych zakresach dat.

Masz dostęp do zestawu narzędzi (tools), które MUSISZ wykorzystać do:
1. Pobierania danych z bazy (fetch_data_for_chart).
2. Wykonywania obliczeń analitycznych (np. calculate_average_speed, calculate_total_distance, calculate_total_energy_per_km).
3. Generowania czytelnych raportów tekstowych (format_analysis_report).
4. Generowania wykresów (generate_single_chart, generate_multi_chart).

**Zasady działania:**
- Zawsze najpierw użyj `get_available_vehicles`, aby sprawdzić, jakie pojazdy są dostępne.
- Aby wykonać analizę lub wygenerować wykres, MUSISZ najpierw użyć `fetch_data_for_chart` z poprawnym `vehicle_id`, `start_date` i `end_date`. Wynik tego narzędzia (string JSON z danymi) przekaż jako argument `data_json` do kolejnych narzędzi.
- Jeśli użytkownik prosi o analizę (np. "ile km przejechał"), użyj narzędzi obliczeniowych, a następnie `format_analysis_report`, aby podsumować wyniki.
- Jeśli użytkownik prosi o wykres (np. "wykres prędkości"), użyj `generate_single_chart` lub `generate_multi_chart`. Pamiętaj, że te narzędzia zwracają string JSON (definicję wykresu Plotly), który musisz przekazać użytkownikowi.
- Zawsze podawaj daty w formacie 'YYYY-MM-DD'.
- Bądź uprzejmy i precyzyjny w odpowiedziach.
"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

# 4. Tworzenie agenta
agent = create_tool_calling_agent(llm, tools, prompt)

# 5. Tworzenie Agent Executor
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

def run_chatbot():
    """Główna pętla interakcji z użytkownikiem."""
    print("--- Chatbot do Analizy Danych Pojazdów ---")
    print("Wpisz 'exit' lub 'quit' aby zakończyć.")
    
    # Pierwsze zapytanie do agenta, aby sprawdził dostępne pojazdy
    initial_query = "Jakie pojazdy są dostępne w bazie danych i w jakim zakresie dat są dane?"
    print(f"\nChatbot: {initial_query}")
    
    try:
        response = agent_executor.invoke({"input": initial_query})
        print(f"Odpowiedź: {response['output']}")
    except Exception as e:
        print(f"Wystąpił błąd podczas inicjalizacji: {e}")
        return

    while True:
        user_input = input("\nTy: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Dziękuję za skorzystanie z chatbota. Do widzenia!")
            break
        
        try:
            # Uruchomienie agenta z zapytaniem użytkownika
            response = agent_executor.invoke({"input": user_input})
            
            # Jeśli agent zwrócił JSON wykresu, informujemy o tym użytkownika
            if "chart" in response['output'].lower() and "json" in response['output'].lower():
                print("\nChatbot: Wygenerowano definicję wykresu w formacie JSON (Plotly). Możesz teraz użyć tego JSON-a do wyświetlenia wykresu w swojej aplikacji webowej lub notatniku.")
                print("--- START WYKRESU JSON ---")
                print(response['output'])
                print("--- KONIEC WYKRESU JSON ---")
            else:
                print(f"\nChatbot: {response['output']}")
                
        except Exception as e:
            print(f"Wystąpił błąd: {e}")
            
if __name__ == "__main__":
    run_chatbot()
