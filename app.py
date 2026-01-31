import os
import json
import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent
from langchain.agents import AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage
import plotly.graph_objects as go
import re
from tools import (
    get_available_vehicles,
    get_available_vehicles_simple,
    get_data_range,
    fetch_data_for_chart,
    format_analysis_report,
    generate_single_chart,
    generate_multi_chart
)

# Wczytanie zmiennych środowiskowych
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY or OPENAI_API_KEY == "TWOJ_KLUCZ_API_GPT":
    st.error("BŁĄD: Uzupełnij klucz OPENAI_API_KEY w pliku .env!")
    st.stop()

# Konfiguracja strony Streamlit
st.set_page_config(
    page_title="Chatbot do Analizy Danych Pojazdów",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🚗 Chatbot do Analizy Danych Pojazdów")
st.markdown("""
Witaj! Jestem asystentem do analizy danych telemetrycznych pojazdów. 
Mogę pomóc Ci w:
- Analizie prędkości i zużycia energii
- Generowaniu wykresów
- Porównywaniu danych między pojazdy
""")

# Inicjalizacja sesji Streamlit
if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent_executor" not in st.session_state:
    # Definicja narzędzi (Tools)
    tools = [
        get_available_vehicles,
        get_data_range,
        fetch_data_for_chart,
        format_analysis_report,
        generate_single_chart,
        generate_multi_chart
    ]

    # Inicjalizacja modelu LLM
    llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0, api_key=OPENAI_API_KEY)

    # Definicja promptu systemowego
    system_prompt = """
Jesteś zaawansowanym asystentem do analizy danych telemetrycznych pojazdów. 
Twoim zadaniem jest odpowiadanie na pytania użytkownika dotyczące prędkości, 
dystansu i zużycia energii pojazdów w określonych zakresach dat.

Masz dostęp do zestawu narzędzi (tools), które MUSISZ wykorzystać do:
1. Pobierania danych z bazy (fetch_data_for_chart).
2. Wykonywania obliczeń analitycznych (format_analysis_report).
3. Generowania wykresów (generate_single_chart, generate_multi_chart).

**Zasady działania:**
- Zawsze najpierw użyj `get_available_vehicles`, aby sprawdzić, jakie pojazdy są dostępne.
- Aby wykonać analizę, MUSISZ najpierw użyć `fetch_data_for_chart` z poprawnym `vehicle_id`, `start_date` i `end_date`.
- Jeśli użytkownik prosi o analizę, użyj `format_analysis_report` do podsumowania wyników.
- Jeśli użytkownik prosi o wykres, użyj `generate_single_chart` lub `generate_multi_chart`.
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

    # Inicjalizacja pamięci agenta
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    # Tworzenie agenta
    agent = create_tool_calling_agent(llm, tools, prompt)

    # Tworzenie Agent Executor z pamięcią
    st.session_state.agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=False,
        handle_parsing_errors=True
    )

# Wyświetlenie historii wiadomości
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # Jeśli wiadomość zawiera wykres (JSON Plotly), wyświetl go
        if message.get("chart"):
            try:
                chart_data = json.loads(message["chart"])
                st.plotly_chart(chart_data, use_container_width=True)
            except:
                st.warning("Nie udało się wyświetlić wykresu.")

# Pole wejściowe dla użytkownika
user_input = st.chat_input("Wpisz swoje pytanie...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Analizuję dane..."):
            try:
                response = st.session_state.agent_executor.invoke({"input": user_input})
                assistant_message = response.get("output", "Nie udało się uzyskać odpowiedzi.")
                
                # Wyświetl tekst odpowiedzi
                st.markdown(assistant_message)
                
                # Sprawdź, czy odpowiedź zawiera ścieżkę do wykresu
                chart_paths = []
                if "/tmp/chart_" in assistant_message:
                    import re
                    chart_paths = re.findall(r'/tmp/chart_\S+\.html', assistant_message)
                    for chart_path in chart_paths:
                        try:
                            with open(chart_path, 'r', encoding='utf-8') as f:
                                chart_html = f.read()
                            st.components.v1.html(chart_html, height=600)
                        except Exception as e:
                            st.warning(f"Nie udało się wyświetlić wykresu: {e}")
                
                # Dodaj odpowiedź do historii (razem z ścieżkami do wykresów)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_message,
                    "chart_paths": chart_paths  # DODAJ TĘ LINIĘ
                })
                
            except Exception as e:
                error_message = f"Błąd: {str(e)}"
                st.error(error_message)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_message,
                    "chart_paths": []  # DODAJ TĘ LINIĘ
                })

# app.py - zmiana w sekcji wyświetlania historii
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # Jeśli wiadomość zawiera wykresy, wyświetl je
        if message.get("chart_paths"):
            for chart_path in message["chart_paths"]:
                try:
                    with open(chart_path, 'r', encoding='utf-8') as f:
                        chart_html = f.read()
                    st.components.v1.html(chart_html, height=600)
                except Exception as e:
                    st.warning(f"Nie udało się wyświetlić wykresu: {e}")

# Sidebar z informacjami
with st.sidebar:
    st.header("📊 Informacje")
    
    if st.button("Wyświetl dostępne pojazdy"):
        try:
            vehicles = get_available_vehicles_simple()
            st.success(f"Dostępne pojazdy: {', '.join(vehicles)}")
        except Exception as e:
            st.error(f"Błąd: {e}")
    
    if st.button("Wyczyść historię czatu"):
        st.session_state.messages = []
        st.success("Historia czatu została wyczyszczona.")
    
    st.markdown("---")
    st.markdown("""
    ### 💡 Przykładowe pytania:
    - "Jakie pojazdy są dostępne?"
    - "Jaka była średnia prędkość dla Pojazd_1 w dniu 2025-02-10?"
    - "Wygeneruj wykres prędkości dla Pojazd_2 w dniu 2025-02-10."
    - "Jakie jest całkowite zużycie energii dla Pojazd_3?"
    """)
