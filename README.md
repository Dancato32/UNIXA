# NEXA Learning Platform

A modern Django-based learning platform with AI-powered features, study materials management, and assignment assistance.

## Features

- 🎨 Modern, clean UI design inspired by contemporary web applications
- 🤖 AI-powered tutor for personalized learning assistance
- 📚 Study materials management system
- ✍️ AI essay generator with web research
- 📝 Assignment completion assistant
- 🎯 Beautiful admin interface powered by Django Jazzmin

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup Instructions

1. **Clone or navigate to the project directory**
   ```bash
   cd nexa
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   
   Create a `.env` file in the project root with:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

5. **Run database migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create a superuser for admin access**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Main site: http://localhost:8000/
   - Admin panel: http://localhost:8000/admin/
   - Dashboard: http://localhost:8000/dashboard/ (after login)

## UI Design

The application features a modern, clean design with:

- **Landing Page**: Gradient hero section with feature cards
- **Dashboard**: Sidebar navigation with clean card-based layout
- **Admin Panel**: Powered by Django Jazzmin with customizable themes
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices

### Color Scheme

- Primary: `#5b4cdb` (Purple)
- Secondary: `#f0f2f5` (Light Gray)
- Text: `#1c1e21` (Dark Gray)
- Accent: Gradient from `#667eea` to `#764ba2`

## Admin Panel Customization

The admin panel uses Django Jazzmin with the following features:

- Modern, responsive interface
- Custom branding and colors
- Icon-based navigation
- Multiple theme options (default: Flatly)
- Quick links to common actions

To change the admin theme, edit `JAZZMIN_SETTINGS` in `nexa/settings.py`:

```python
JAZZMIN_SETTINGS = {
    "theme": "flatly",  # Options: default, cerulean, cosmo, darkly, flatly, etc.
    # ... other settings
}
```

## Project Structure

```
nexa/
├── ai_tutor/          # AI chat and essay generation
├── assignment/        # Assignment management
├── dashboard/         # Main dashboard
├── materials/         # Study materials management
├── users/            # User authentication and profiles
├── nexa/             # Project settings
├── media/            # Uploaded files
├── requirements.txt  # Python dependencies
└── manage.py         # Django management script
```

## Technologies Used

- **Backend**: Django 4.2+
- **Admin UI**: Django Jazzmin
- **AI**: OpenAI API
- **File Processing**: PyPDF2, python-docx, python-pptx
- **Frontend**: HTML5, CSS3 (embedded)
- **Database**: SQLite (development)

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is for educational purposes.
