from django.urls import path
from . import views

urlpatterns = [
    # API routes MUST come before wildcard subject/topic routes
    path('api/ai-teach/', views.api_ai_teach, name='api_ai_teach'),
    path('api/book-teach/', views.api_book_teach, name='api_book_teach'),
    path('api/quiz/', views.api_quiz, name='api_quiz'),
    path('api/grade/', views.api_grade, name='api_grade'),
    path('api/podcast/', views.api_podcast, name='api_podcast'),
    path('api/teach/', views.api_teach, name='api_teach'),
    # Pages
    path('', views.library_home, name='library_home'),
    path('<str:subject_key>/', views.subject_page, name='library_subject'),
    path('<str:subject_key>/level/<str:level_slug>/', views.level_page, name='library_level'),
    path('<str:subject_key>/<str:topic_slug>/', views.topic_page, name='library_topic'),
]
