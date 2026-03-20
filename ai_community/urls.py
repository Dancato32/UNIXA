from django.urls import path
from ai_community import views

app_name = 'ai_community'

urlpatterns = [
    # Hub
    path('', views.ai_hub, name='hub'),
    path('startup/', views.startup_page, name='startup'),

    # APIs
    path('api/profile/', views.save_ai_profile, name='save_profile'),
    path('api/find-people/', views.find_people, name='find_people'),
    path('api/assistant/', views.campus_assistant, name='assistant'),
    path('api/study-group/', views.create_study_group, name='study_group'),
    path('api/study-group/<uuid:ws_id>/join/', views.join_study_group, name='join_study_group'),
    path('api/startup/create/', views.create_startup, name='create_startup'),
    path('api/startup/<uuid:team_id>/respond/', views.respond_startup_invite, name='respond_invite'),
    path('api/opportunities/', views.opportunities, name='opportunities'),
    path('api/opportunities/scan/', views.scan_opportunities, name='scan_opportunities'),
    path('api/icebreaker/<str:username>/', views.get_icebreaker, name='icebreaker'),
]
