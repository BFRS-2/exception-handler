# ConversationalAgent: Automated Shipment Exception Resolution

This project automates the classification and resolution of shipment exceptions (e.g., address issues, failed deliveries) using shipment logs and seller-agent conversation history. It leverages AI agents, LangChain, and ChromaDB to recommend or autonomously resolve issues with minimal human intervention.

## Features
- Exception classification from logs and conversations
- Contextual retrieval using ChromaDB
- AI agent-driven action recommendation and resolution
- Simple Streamlit chatbot interface

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set your OpenAI API key as an environment variable:
   ```bash
   export OPENAI_API_KEY=your-key-here
   ```
3. Run the app:
   ```bash
   streamlit run app.py
   ```

## Directory Structure
```
ConversationalAgent/
├── data/
│   ├── shipment_logs.csv
│   └── conversations.json
├── agents/
│   └── exception_agent.py
├── tools/
│   └── shipment_tools.py
├── vectorstore/
│   └── chroma_db.py
├── app.py
├── requirements.txt
└── README.md
``` 