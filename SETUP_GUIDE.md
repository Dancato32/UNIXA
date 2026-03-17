# NEXA Setup Guide

## Quick Start

### Windows Users

1. **Double-click `install.bat`** - This will automatically:
   - Create a virtual environment
   - Install all dependencies
   - Set up the database
   - Prompt you to create an admin user

2. **Edit the `.env` file** and add your OpenAI API key:
   ```
   OPENAI_API_KEY=sk-your-actual-key-here
   ```

3. **Start the server**:
   ```bash
   venv\Scripts\activate
   python manage.py runserver
   ```

### macOS/Linux Users

1. **Run the install script**:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

2. **Edit the `.env` file** and add your OpenAI API key:
   ```
   OPENAI_API_KEY=sk-your-actual-key-here
   ```

3. **Start the server**:
   ```bash
   source venv/bin/activate
   python manage.py runserver
   ```

## Manual Installation

If the automated scripts don't work, follow these steps:

### 1. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create a `.env` file in the project root:

```
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. Set Up Database

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Admin User

```bash
python manage.py createsuperuser
```

Follow the prompts to create your admin account.

### 6. Run the Server

```bash
python manage.py runserver
```

## Accessing the Application

Once the server is running, open your browser and visit:

- **Landing Page**: http://localhost:8000/
- **Admin Panel**: http://localhost:8000/admin/
- **Dashboard**: http://localhost:8000/dashboard/ (requires login)

## Admin Panel Features

The admin panel (powered by Django Jazzmin) includes:

- User management
- Study materials management
- AI conversation history
- Essay requests tracking
- Assignment management

### Customizing the Admin Theme

Edit `nexa/settings.py` and modify the `JAZZMIN_SETTINGS` dictionary:

```python
JAZZMIN_SETTINGS = {
    "theme": "flatly",  # Change this to any supported theme
    # Available themes: default, cerulean, cosmo, cyborg, darkly, 
    # flatly, journal, litera, lumen, lux, materia, minty, pulse, 
    # sandstone, simplex, slate, solar, spacelab, superhero, united, yeti
}
```

## Troubleshooting

### Issue: "No module named 'jazzmin'"

**Solution**: Make sure you've installed all dependencies:
```bash
pip install -r requirements.txt
```

### Issue: "OPENAI_API_KEY not found"

**Solution**: Create a `.env` file in the project root with your API key:
```
OPENAI_API_KEY=sk-your-actual-key-here
```

### Issue: Database errors

**Solution**: Delete `db.sqlite3` and run migrations again:
```bash
# Windows
del db.sqlite3
python manage.py migrate

# macOS/Linux
rm db.sqlite3
python manage.py migrate
```

### Issue: Static files not loading

**Solution**: Collect static files:
```bash
python manage.py collectstatic
```

## Development Tips

### Running Tests

```bash
python manage.py test
```

### Creating New Apps

```bash
python manage.py startapp app_name
```

### Database Shell

```bash
python manage.py dbshell
```

### Django Shell

```bash
python manage.py shell
```

## Production Deployment

For production deployment, you'll need to:

1. Set `DEBUG = False` in settings.py
2. Configure `ALLOWED_HOSTS`
3. Use a production database (PostgreSQL recommended)
4. Set up a proper web server (Gunicorn + Nginx)
5. Configure static file serving
6. Set up SSL/HTTPS
7. Use environment variables for sensitive data

## Getting Help

If you encounter any issues:

1. Check the Django documentation: https://docs.djangoproject.com/
2. Check Django Jazzmin docs: https://django-jazzmin.readthedocs.io/
3. Review the error messages carefully
4. Check the console/terminal output for detailed error information

## Next Steps

After installation:

1. Log in to the admin panel and explore the interface
2. Create a regular user account from the landing page
3. Upload some study materials
4. Try the AI tutor chat feature
5. Generate an essay or complete an assignment

Enjoy using NEXA! 🚀
