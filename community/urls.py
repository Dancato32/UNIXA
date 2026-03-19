"""
URL configuration for the community app.
Template pages + REST API, all under /community/
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from community import views
from community.viewsets import (
    BlockViewSet,
    CommentViewSet,
    ConversationViewSet,
    CustomCommunityViewSet,
    FeedViewSet,
    FollowViewSet,
    NotificationViewSet,
    PostViewSet,
    SchoolCommunityViewSet,
    SpaceViewSet,
)

app_name = 'community'

# ── DRF API router ────────────────────────────────────────────────────────────
router = DefaultRouter()
router.register(r'school-communities', SchoolCommunityViewSet, basename='school-community')
router.register(r'custom-communities', CustomCommunityViewSet, basename='custom-community')
router.register(r'posts', PostViewSet, basename='post')
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'follows', FollowViewSet, basename='follow')
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'feed', FeedViewSet, basename='feed')
router.register(r'spaces', SpaceViewSet, basename='space')
router.register(r'blocks', BlockViewSet, basename='block')

# ── Template URL patterns ─────────────────────────────────────────────────────
urlpatterns = [
    # Feed
    path('', views.feed, name='feed'),

    # School communities
    path('schools/', views.schools, name='schools'),
    path('schools/<slug:slug>/', views.school_detail, name='school_detail'),
    path('schools/<slug:slug>/join/', views.school_join, name='school_join'),
    path('schools/<slug:slug>/leave/', views.school_leave, name='school_leave'),

    # Custom communities
    path('communities/', views.custom_list, name='custom_list'),
    path('communities/create/', views.custom_create, name='custom_create'),
    path('communities/<slug:slug>/', views.custom_detail, name='custom_detail'),

    # Posts
    path('posts/create/', views.post_create, name='post_create'),
    path('posts/<uuid:pk>/', views.post_detail, name='post_detail'),
    path('posts/<uuid:pk>/delete/', views.post_delete, name='post_delete'),

    # Comment likes
    path('comments/<uuid:comment_id>/like/', views.comment_like, name='comment_like'),

    # Community profiles
    path('profile/edit/me/', views.community_profile_edit, name='profile_edit'),
    path('profile/<str:username>/', views.community_profile, name='profile'),

    # Messages
    path('messages/', views.messages_view, name='messages'),
    path('messages/<uuid:convo_id>/', views.messages_view, name='conversation_detail'),
    path('messages/<uuid:convo_id>/voice/', views.send_voice_note, name='send_voice_note'),
    path('messages/<uuid:convo_id>/media/', views.send_media, name='send_media'),
    path('messages/<uuid:convo_id>/call/', views.create_call, name='create_call'),
    path('messages/<uuid:convo_id>/poll/', views.poll_messages, name='poll_messages'),
    path('messages/new/', views.conversation_create, name='conversation_create'),
    path('dm/<str:username>/', views.dm_start, name='dm_start'),

    # Notifications
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/mark-read/', views.notifications_mark_read, name='notifications_mark_read'),

    # REST API
    path('api/', include(router.urls)),
]
