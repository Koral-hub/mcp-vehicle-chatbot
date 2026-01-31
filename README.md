# MCP Vehicle Chatbot

Chatbot oparty na **LangChain + MCP (Model Context Protocol)** do analizy metryk pojazdów (np. zużycie paliwa, zasięg, koszty) z automatycznym generowaniem wykresów.

## 🎯 Funkcjonalności
- **Rozmowa z AI**: Pytaj o dane pojazdów (np. "Porównaj zasięg Tesla Model 3 vs BMW i4").
- **Streamlit UI**: Pełny interfejs webowy z chatem, historią rozmów i streaming odpowiedzi.
- **Historia konwersacji**: Session_state przechowuje kontekst (wielokrotne pytania w jednej sesji).
- **Wykresy**: Automatyczne generowanie chartów (Plotly/Altair) dla metryk (np. koszt/km vs prędkość).
- **MCP Tools**: Dynamiczne narzędzia do obliczeń (np. symulacja jazdy, kalkulacja baterii EV).
- **Docker**: Łatwe uruchomienie lokalnie lub deploy.

## 🛠️ Architektura
mcp-vehicle-chatbot/
├── app/ # Backend LangChain + MCP
│ ├── chain.py # LangChain chain z MCP tools
│ ├── tools.py # MCP tools (metrics, charts)
│ └── config.py # Env vars (OPENAI_API_KEY)
├── streamlit/ # Frontend UI
│ └── ui.py # Streamlit app z chat history
├── docker-compose.yml # Stack: app + MCP server
├── requirements.txt # Python deps
└── .env.example # Konfiguracja


## 🚀 Szybki start (Docker)
```bash
git clone https://github.com/Koral-hub/mcp-vehicle-chatbot
cd mcp-vehicle-chatbot
cp .env.example .env  # Dodaj OPENAI_API_KEY
docker compose up     # Streamlit: http://localhost:8501
```
## 🐍 Lokalnie (Python)
```bash
pip install -r requirements.txt
streamlit run streamlit/ui.py
```
## 🔧 Konfiguracja

```text
OPENAI_API_KEY=sk-...
MCP_SERVER_URL=http://localhost:8000  # MCP backend

```

## 📊 Przykłady użycia
"Oblicz zasięg Pojazd_1 na w dniach 12-13 grudnia"
"Wygeneruj wykres zużycia energii"
"Zrób raport dla tych aut i podaj ich średnią prędkość"

## 🏗️ Tech stack
LLM: OpenAI GPT-4o / Grok
LangChain: Chains + MCP integration
UI: Streamlit + Plotly
MCP: Tools dla vehicle metrics
Deploy: Docker Compose

## 🤝 Kontrybucje
Fork → PR. Tests mile widziane!

## 📄 Licencja
MIT
