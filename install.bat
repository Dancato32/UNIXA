@echo off
echo =========================================
echo NEXA Learning Platform - Installation
echo =========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo X Python is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

echo √ Python found
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo.
echo Installing dependencies...
pip install -r requirements.txt

REM Check if .env file exists
if not exist .env (
    echo.
    echo Creating .env file...
    echo OPENAI_API_KEY=your_openai_api_key_here > .env
    echo ! Please edit .env file and add your OpenAI API key
)

REM Run migrations
echo.
echo Running database migrations...
python manage.py makemigrations
python manage.py migrate

REM Create superuser prompt
echo.
echo =========================================
echo Create Admin Superuser
echo =========================================
echo You'll need this to access the admin panel at /admin/
echo.
python manage.py createsuperuser

echo.
echo =========================================
echo Installation Complete! 🎉
echo =========================================
echo.
echo To start the development server:
echo   1. Activate virtual environment: venv\Scripts\activate
echo   2. Run server: python manage.py runserver
echo.
echo Then visit:
echo   - Main site: http://localhost:8000/
echo   - Admin panel: http://localhost:8000/admin/
echo.
echo Don't forget to add your OpenAI API key to the .env file!
echo.
pause
