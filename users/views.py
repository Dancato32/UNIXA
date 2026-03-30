from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
import threading

User = get_user_model()


def landing_view(request):
    """Landing page view - redirect to community feed if logged in."""
    if request.user.is_authenticated:
        return redirect('community:feed') 
    return render(request, 'users/landing_final.html')


def login_view(request):
    """User login view - redirects to community feed after login."""
    if request.user.is_authenticated:
        return redirect('community:feed') 

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('community:feed')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please enter both username and password.')

    return render(request, 'users/register_split.html')


def register_view(request):
    """User registration view - redirects to community feed after signup."""
    if request.user.is_authenticated:
        return redirect('community:feed')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        errors = []

        # Validation
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

        # Create user
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )

            # Send admin notification asynchronously
            def _send_notification():
                try:
                    from django.core.mail import send_mail
                    send_mail(
                        subject=f'New signup: {username}',
                        message=(
                            f'A new user just signed up on Nexa!\n\n'
                            f'Username: {username}\n'
                            f'Email:    {email}\n'
                            f'Time:     {timezone.now().strftime("%Y-%m-%d %H:%M UTC")}\n'
                        ),
                        from_email=settings.EMAIL_HOST_USER,
                        recipient_list=[settings.ADMIN_NOTIFICATION_EMAIL],
                        fail_silently=True,
                    )
                except Exception:
                    pass

            threading.Thread(target=_send_notification, daemon=True).start()

            # Login the new user
            auth_user = authenticate(request, username=username, password=password)
            if auth_user is not None:
                login(request, auth_user)
            else:
                # fallback
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)

            # Redirect to community feed after signup
            return redirect('community:feed')

        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return render(request, 'users/register_split.html')

    return render(request, 'users/register_split.html')


def logout_view(request):
    """User logout view - redirects to landing page."""
    logout(request)
    return redirect('landing')