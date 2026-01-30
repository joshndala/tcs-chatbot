#!/bin/bash

# Run TCS Multi-Agent Chatbot with proper virtual environment

echo "🚀 Starting TCS Multi-Agent Chatbot..."
echo ""

# Cleanup previous session data
echo "🧹 Cleaning up previous session data..."
if [ -d "data/pdfs" ]; then
    rm -rf data/pdfs/*
    echo "   - PDFs cleared"
fi

if [ -d "data/embeddings" ]; then
    rm -rf data/embeddings/*
    echo "   - Embeddings cleared"
fi
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run ./setup.sh first"
    exit 1
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo "Please copy .env.example to .env and add your GOOGLE_API_KEY"
    echo ""
fi

# Run Streamlit
echo "▶️  Launching Streamlit app..."
echo ""
streamlit run app.py
