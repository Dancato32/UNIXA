from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('', views.landing_view, name='landing'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('onboarding/', views.onboarding_view, name='onboarding'),
    path('onboarding/complete-tutorial/', views.mark_tutorial_complete, name='mark_tutorial_complete'),
    path('privacy/', TemplateView.as_view(template_name='users/privacy.html'), name='privacy'),
    path('terms/', TemplateView.as_view(template_name='users/terms.html'), name='terms'),
    path('security/', TemplateView.as_view(template_name='users/security.html'), name='security'),
]
