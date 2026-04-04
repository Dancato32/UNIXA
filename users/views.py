from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import threading

User = get_user_model()


def landing_view(request):
    """Landing page view - redirect to feed if logged in."""
    if request.user.is_authenticated:
        return redirect('community:feed')
    return render(request, 'users/landing_new.html')


def login_view(request):
    """User login view - redirects to dashboard after login."""
    if request.user.is_authenticated:
        return redirect('community:feed')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                if getattr(user, 'onboarding_complete', False):
                    return redirect('community:feed')
                else:
                    return redirect('/onboarding/')
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

            # Redirect according to onboarding status
            if getattr(auth_user, 'onboarding_complete', False):
                return redirect('/dashboard/')
            else:
                # Always route to onboarding via absolute path to avoid namespace issues
                return redirect('/onboarding/')

        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return render(request, 'users/register_split.html')

    return render(request, 'users/register_split.html')


def logout_view(request):
    """User logout view - redirects to landing page."""
    logout(request)
    return redirect('landing')
def onboarding_view(request):
    """One-time onboarding flow for new users."""
    if not request.user.is_authenticated:
        return redirect('login')
    if request.method == 'POST':
        # Safely get community_profile if it exists
        if hasattr(request.user, 'community_profile'):
            profile = request.user.community_profile
            # Save any fields from the form
            display_name = request.POST.get('display_name')
            bio = request.POST.get('bio')
            major = request.POST.get('major')
            interests = request.POST.get('interests')
            match_prefs = request.POST.get('match_prefs')
            
            if display_name:
                profile.display_name = display_name
            if bio:
                profile.bio = bio
            if major:
                profile.major = major
            if interests:
                profile.interests = interests
            if match_prefs:
                profile.match_prefs = match_prefs
            profile.save()
        
        # Mark onboarding complete and go to feed with ?welcome=1 for splash/tutorial
        u = request.user
        u.onboarding_complete = True
        u.save(update_fields=['onboarding_complete'])
        return redirect('/community/?welcome=1')
    return render(request, 'users/onboarding.html')

@csrf_exempt
def mark_tutorial_complete(request):
    """Mark the community tour as complete for the current user."""
    if request.user.is_authenticated:
        request.user.tutorial_complete = True
        request.user.save(update_fields=['tutorial_complete'])
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error', 'message': 'Not authenticated'}, status=401)
