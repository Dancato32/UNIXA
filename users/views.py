from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib import messages

User = get_user_model()


def landing_view(request):
    """Landing page view - accessible only to unauthenticated users."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'users/landing_final.html')


def login_view(request):
    """User login view."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please enter both username and password.')
    
    return render(request, 'users/register_split.html')


def register_view(request):
    """User registration view."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        errors = []
        
        if not username:
            errors.append('Username is required.')
        elif User.objects.filter(username=username).exists():
            errors.append('Username already exists.')
        
        if not email:
            errors.append('Email is required.')
        elif User.objects.filter(email=email).exists():
            errors.append('Email already registered.')
        
        if not password:
            errors.append('Password is required.')
        elif len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'users/register_split.html')
        
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            # Send signup notification to admin
            try:
                from django.core.mail import send_mail
                from django.conf import settings
                from django.utils import timezone
                send_mail(
                    subject=f'🎉 New signup: {username}',
                    message=(
                        f'A new user just signed up on Nexa!\n\n'
                        f'Username: {username}\n'
                        f'Email:    {email}\n'
                        f'Time:     {timezone.now().strftime("%Y-%m-%d %H:%M UTC")}\n\n'
                        f'Total users: {User.objects.count()}\n'
                    ),
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[settings.ADMIN_NOTIFICATION_EMAIL],
                    fail_silently=True,  # never crash signup if email fails
                )
            except Exception:
                pass  # email is best-effort
            login(request, user)
            return redirect('dashboard')
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return render(request, 'users/register_split.html')
    
    return render(request, 'users/register_split.html')


def logout_view(request):
    """User logout view."""
    logout(request)
    return redirect('landing')

