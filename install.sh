#!/bin/bash

echo "========================================="
echo "NEXA Learning Platform - Installation"
echo "========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✓ Python 3 found"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file..."
    echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
    echo "⚠️  Please edit .env file and add your OpenAI API key"
fi

# Run migrations
echo ""
echo "Running database migrations..."
python manage.py makemigrations
python manage.py migrate

# Create superuser prompt
echo ""
echo "========================================="
echo "Create Admin Superuser"
echo "========================================="
echo "You'll need this to access the admin panel at /admin/"
echo ""
python manage.py createsuperuser

echo ""
echo "========================================="
echo "Installation Complete! 🎉"
echo "========================================="
echo ""
echo "To start the development server:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run server: python manage.py runserver"
echo ""
echo "Then visit:"
echo "  - Main site: http://localhost:8000/"
echo "  - Admin panel: http://localhost:8000/admin/"
echo ""
echo "Don't forget to add your OpenAI API key to the .env file!"
echo ""
