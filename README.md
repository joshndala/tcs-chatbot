# Executive Assistant for John
### Customer Support Analytics & Policy Search

A multi-agent AI system built with LangGraph to help John query customer support data and company policies using natural language.

## Overview

This system enables John to:
- **Query customer support tickets** using natural language (SQL-backed)
- **Search company policies** from uploaded PDF documents (RAG-backed)
- **Get analytics** on ticket resolution times, customer satisfaction, and more

## Technology Stack

- **LangGraph**: Multi-agent orchestration
- **Google Gemini 3 Flash Preview**: LLM for reasoning and query generation
- **SQLite**: Customer and ticket data storage
- **ChromaDB**: Vector database for policy documents
- **Streamlit**: Interactive web interface
- **LangChain**: Agent framework and tools

## Architecture

### Two Specialized Agents

1. **AccountAgent**: Handles structured data queries
   - Generates SQL queries from natural language
   - Queries customer profiles and support tickets
   - Provides analytics and insights

2. **PolicyAgent**: Handles unstructured data queries
   - Uses RAG (Retrieval Augmented Generation)
   - Searches company policy documents
   - Answers policy-related questions

### Router

Intelligent query classification to route questions to the appropriate agent.

## Setup

### Prerequisites

- Python 3.9+
- Google AI API key ([Get one here](https://makersuite.google.com/app/apikey))
- Kaggle API credentials (for dataset download)

### Installation

1. **Clone the repository**
   ```bash
   cd tcs-chatbot
   ```

2. **Set up Kaggle API** (if not already configured)
   ```bash
   # Place your kaggle.json in ~/.kaggle/
   mkdir -p ~/.kaggle
   # Download kaggle.json from https://www.kaggle.com/settings
   mv ~/Downloads/kaggle.json ~/.kaggle/
   chmod 600 ~/.kaggle/kaggle.json
   ```

3. **Run setup script**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

   This will:
   - Create a virtual environment
   - Install dependencies
   - Download Kaggle customer support dataset
   - Set up the database
   - Ingest ticket data

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your GOOGLE_API_KEY
   ```

### Manual Setup (Alternative)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download Kaggle dataset
python scripts/download_kaggle_data.py

# Ingest data
python scripts/ingest_kaggle_data.py

# Set up environment
cp .env.example .env
# Add your GOOGLE_API_KEY to .env
```

## Running the Application

```bash
./run.sh
```

**Note:** The `./run.sh` script automatically **clears all uploaded PDFs and embeddings** to ensure a fresh session. To persist data across runs, use `streamlit run app.py` manually.

## Usage

### Uploading Policy Documents

1. Click the sidebar "Upload Policy PDFs" section
2. Upload company policy documents (PDF format)
3. Documents are automatically processed and indexed using **PyMuPDF** (high-speed extraction)
4. Uploaded documents appear immediately in the "📚 Uploaded Documents" section

### Managing Policy Documents

- **View uploaded documents**: Check the "📚 Uploaded Documents" section at the top of the sidebar
- **Delete documents**: Click the "🗑️ Delete File" button next to any document
  - Removes file from disk and vector database
  - Clears the upload widget automatically

### Asking Questions

**Customer Support Queries:**
- "Show breakdown of Refund requests by Product"
- "Avg resolution time for Technical issues with GoPro Hero"
- "Identify customers with multiple Critical tickets"

**Policy Queries:**
- "What does our refund policy say?"
- "Explain the customer support escalation process"

### Features

- **Smart Agents**: The system parses the database schema on startup to "learn" valid values (e.g., ticket priorities), preventing hallucinations.
- **Document Management**: Upload and delete policy PDFs with automatic cleanup from disk and vector database
- **Clean UI**: Streamlined interface with hidden redundant file lists and optimized sidebar layout
- **Safety**: Configured to allow SQL generation without triggering false-positive safety blocks.
- **Conversation History**: Follow-up questions understand context
- **Debug Mode**: View SQL queries and retrieved document chunks

## Project Structure

```
tcs-chatbot/
├── agents/              # Agent implementations
│   ├── account_agent.py # SQL agent (with dynamic schema discovery)
│   ├── policy_agent.py  # RAG agent (with safety config)
│   ├── graph.py         # LangGraph workflow
│   └── state.py         # State management
├── database/            # Data layer
│   ├── schema.sql       # Database schema
│   ├── sqlite_manager.py # SQLite interface (dynamic schema discovery)
│   └── vector_store.py  # ChromaDB interface (with delete_by_metadata)
├── scripts/             # Utility scripts
│   ├── download_kaggle_data.py  # Dataset download
│   └── ingest_kaggle_data.py    # Data ingestion
├── tests/               # Test suite
│   └── verify_system.py # System verification tests
├── utils/               # Utilities
│   ├── prompts.py       # LLM prompts (with CoT for router)
│   └── pdf_processor.py # PDF processing (PyMuPDF + LangChain)
├── config/              # Configuration
│   └── settings.py      # App settings
├── data/                # Data storage
│   ├── kaggle/          # Kaggle dataset
│   ├── pdfs/            # Policy PDFs
│   └── customers.db     # SQLite database
├── app.py               # Streamlit interface
└── requirements.txt     # Dependencies
```

## Configuration

Key settings in `.env`:

```env
GOOGLE_API_KEY=your_api_key_here
MODEL_NAME=gemini-3-flash-preview
TEMPERATURE=0.1  # Low temperature for precise code generation
CHUNK_SIZE=1800
CHUNK_OVERLAP=200
```

## Dataset

Uses the [Customer Support Ticket Dataset](https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset) from Kaggle.

**Schema:**
- **Customers**: profiles, demographics, purchase history
- **Tickets**: support tickets with status, priority, resolution times, satisfaction ratings

## Development

### Adding New Policies

Upload PDF files via the UI sidebar. Files are stored in `data/pdfs/` and automatically indexed.

### Customizing Agents

- **Prompts**: Edit `utils/prompts.py`
- **Agent Logic**: Modify `agents/account_agent.py` or `agents/policy_agent.py`
- **Routing**: Update `agents/graph.py`

### Database Schema

See `database/schema.sql` for the current schema. To reset:

```bash
rm data/customers.db
python scripts/ingest_kaggle_data.py
```

## Troubleshooting

**"No module named 'langgraph'"**
- Make sure virtual environment is activated: `source venv/bin/activate`
- Or use `./run.sh` which activates automatically

**Kaggle dataset download fails**
- Ensure `~/.kaggle/kaggle.json` exists and has correct permissions
- Accept dataset terms on Kaggle website

**Empty database**
- Run `python scripts/ingest_kaggle_data.py` to load data

## License

MIT

## Acknowledgments

- Dataset: [Kaggle Customer Support Tickets](https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset)
