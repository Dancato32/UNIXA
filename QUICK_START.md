# NEXA Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Install Dependencies

**Windows:**
```bash
# Double-click install.bat or run:
install.bat
```

**macOS/Linux:**
```bash
chmod +x install.sh
./install.sh
```

### Step 2: Add Your OpenAI API Key

Edit the `.env` file that was created:
```
OPENAI_API_KEY=sk-your-actual-key-here
```

### Step 3: Start the Server

**Windows:**
```bash
venv\Scripts\activate
python manage.py runserver
```

**macOS/Linux:**
```bash
source venv/bin/activate
python manage.py runserver
```

## 🎯 Access Points

Once running, visit:

- **Landing Page**: http://localhost:8000/
- **Admin Panel**: http://localhost:8000/admin/
- **Dashboard**: http://localhost:8000/dashboard/ (after login)

## 🎨 What's New?

### Modern UI Design
- ✨ Gradient hero sections with purple/blue tones
- 🎯 Clean, card-based layouts
- 📱 Fully responsive design
- 🎭 Beautiful admin interface with Django Jazzmin

### Key Features
- 🤖 AI-powered tutor chat
- 📚 Study materials management
- ✍️ AI essay generator
- 📝 Assignment completion assistant
- 👨‍💼 Professional admin panel

## 🔧 Admin Panel

### First Time Setup

1. Create a superuser (done during installation)
2. Visit http://localhost:8000/admin/
3. Log in with your superuser credentials

### Admin Features

- **Theme Customization**: Choose from 20+ themes
- **User Management**: Add/edit users and permissions
- **Content Management**: Manage all app data
- **Icon Navigation**: Easy-to-use sidebar with icons
- **Quick Actions**: Fast access to common tasks

### Changing the Admin Theme

Edit `nexa/settings.py`:

```python
JAZZMIN_SETTINGS = {
    "theme": "flatly",  # Try: darkly, cosmo, cyborg, etc.
}
```

Available themes:
- `flatly` (default) - Clean and modern
- `darkly` - Dark mode
- `cosmo` - Bright and friendly
- `cyborg` - Dark with blue accents
- `lux` - Elegant and sophisticated
- And 15+ more!

## 📱 Using the Platform

### For Students

1. **Register**: Create an account from the landing page
2. **Upload Materials**: Add your study materials (PDF, Word, PowerPoint)
3. **Chat with AI**: Ask questions and get instant help
4. **Generate Essays**: Use AI to research and write essays
5. **Complete Assignments**: Upload assignments for AI assistance

### For Administrators

1. **User Management**: Add/remove users, assign permissions
2. **Content Moderation**: Review and manage user content
3. **System Monitoring**: Track usage and performance
4. **Configuration**: Customize settings and themes

## 🎓 Tips & Tricks

### Best Practices

1. **Upload Quality Materials**: Better materials = better AI responses
2. **Be Specific**: Ask clear, specific questions to the AI tutor
3. **Review AI Output**: Always review and edit AI-generated content
4. **Organize Materials**: Use descriptive titles and subjects

### Keyboard Shortcuts (Admin)

- `Ctrl/Cmd + K`: Quick search
- `Ctrl/Cmd + S`: Save changes
- `Esc`: Close modals

## 🐛 Troubleshooting

### Common Issues

**Issue**: Can't access admin panel
- **Solution**: Make sure you created a superuser during installation

**Issue**: AI features not working
- **Solution**: Check that your OpenAI API key is correctly set in `.env`

**Issue**: Static files not loading
- **Solution**: Run `python manage.py collectstatic`

**Issue**: Database errors
- **Solution**: Delete `db.sqlite3` and run `python manage.py migrate` again

### Getting Help

1. Check `SETUP_GUIDE.md` for detailed instructions
2. Review `UI_UPDATES.md` for design documentation
3. Check Django docs: https://docs.djangoproject.com/
4. Check Jazzmin docs: https://django-jazzmin.readthedocs.io/

## 📊 Project Structure

```
nexa/
├── ai_tutor/          # AI chat & essay generation
├── assignment/        # Assignment management
├── dashboard/         # Main dashboard
├── materials/         # Study materials
├── users/            # Authentication
├── nexa/             # Settings
├── media/            # Uploaded files
└── manage.py         # Django CLI
```

## 🔐 Security Notes

### For Development

- Default SQLite database (fine for development)
- Debug mode enabled
- Secret key in settings (change for production)

### For Production

Before deploying to production:

1. Set `DEBUG = False`
2. Change `SECRET_KEY`
3. Configure `ALLOWED_HOSTS`
4. Use PostgreSQL or MySQL
5. Set up proper web server (Gunicorn + Nginx)
6. Enable HTTPS
7. Use environment variables for secrets

## 🎉 Next Steps

After getting started:

1. ✅ Explore the admin panel
2. ✅ Create a test user account
3. ✅ Upload sample study materials
4. ✅ Try the AI tutor chat
5. ✅ Generate a test essay
6. ✅ Customize the admin theme
7. ✅ Review the codebase

## 📚 Additional Resources

- **README.md**: Project overview and features
- **SETUP_GUIDE.md**: Detailed installation guide
- **UI_UPDATES.md**: Design changes documentation
- **requirements.txt**: Python dependencies

## 💡 Pro Tips

1. **Backup Regularly**: Keep backups of your database
2. **Test Changes**: Use a separate development environment
3. **Monitor Logs**: Check console output for errors
4. **Update Dependencies**: Keep packages up to date
5. **Customize**: Make it your own - change colors, add features!

---

**Need Help?** Check the documentation files or review the error messages in your console.

**Ready to Deploy?** See SETUP_GUIDE.md for production deployment instructions.

**Want to Contribute?** Feel free to submit issues and pull requests!

🚀 Happy Learning with NEXA!
