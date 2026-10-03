#!/bin/bash
# ScanNifty100 Bootstrap Script
# Sets up the development environment

set -e

echo "=== ScanNifty100 Bootstrap ==="

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "Please update .env with your configuration"
fi

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements/dev.txt

# Create data directories
echo "Creating data directories..."
mkdir -p data/raw data/staging data/clean data/reference data/samples

echo "=== Bootstrap Complete ==="
echo "Run 'source venv/bin/activate' to activate the environment"
echo "Then run 'docker-compose up -d' to start services"
