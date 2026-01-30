#!/bin/bash

# Setup script for Executive Assistant for John
# Customer Support Analytics & Policy Search System

set -e  # Exit on error

echo "🚀 Setting up Executive Assistant for John..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📥 Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Check for Kaggle credentials
if [ ! -f "$HOME/.kaggle/kaggle.json" ]; then
    echo ""
    echo "⚠️  Kaggle API credentials not found!"
    echo "Please set up Kaggle API:"
    echo "1. Go to https://www.kaggle.com/settings"
    echo "2. Create new API token"
    echo "3. Place kaggle.json in ~/.kaggle/"
    echo "4. Run: chmod 600 ~/.kaggle/kaggle.json"
    echo ""
    read -p "Do you want to continue without downloading the dataset? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    SKIP_DATASET=true
else
    echo "✓ Kaggle credentials found"
    SKIP_DATASET=false
fi

# Download Kaggle dataset
if [ "$SKIP_DATASET" = false ]; then
    echo "📥 Downloading Kaggle customer support dataset..."
    python scripts/download_kaggle_data.py
    
    if [ $? -ne 0 ]; then
        echo "⚠️  Dataset download failed. You can download it manually later."
        SKIP_INGEST=true
    else
        SKIP_INGEST=false
    fi
else
    SKIP_INGEST=true
fi

# Remove old database if it exists
if [ -f "data/customers.db" ]; then
    echo "🗑️  Removing old database..."
    rm data/customers.db
fi

# Create database schema
echo "🗄️  Creating database schema..."
sqlite3 data/customers.db < database/schema.sql

# Ingest data
if [ "$SKIP_INGEST" = false ]; then
    echo "📊 Ingesting customer support data..."
    python scripts/ingest_kaggle_data.py
    
    if [ $? -ne 0 ]; then
        echo "⚠️  Data ingestion failed. Please check the error messages above."
    fi
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your GOOGLE_API_KEY"
    echo "Get your API key from: https://makersuite.google.com/app/apikey"
    echo ""
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your GOOGLE_API_KEY (if not already done)"
echo "2. Run: ./run.sh"
echo "3. Upload company policy PDFs via the sidebar"
echo "4. Start asking questions!"
echo ""
