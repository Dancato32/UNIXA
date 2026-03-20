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
    path('communities/<slug:slug>/delete/', views.custom_delete, name='custom_delete'),

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
    path('messages/<uuid:convo_id>/peer/', views.get_peer_id, name='get_peer_id'),
    path('messages/<uuid:convo_id>/poll/', views.poll_messages, name='poll_messages'),
    path('messages/new/', views.conversation_create, name='conversation_create'),
    path('dm/<str:username>/', views.dm_start, name='dm_start'),

    # Notifications
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/mark-read/', views.notifications_mark_read, name='notifications_mark_read'),

    # Group Workspaces
    path('workspaces/', views.workspace_list, name='workspace_list'),
    path('workspaces/create/', views.workspace_create, name='workspace_create'),
    path('workspaces/join/<str:invite_code>/', views.workspace_join, name='workspace_join'),
    path('workspaces/users/search/', views.workspace_search_users, name='workspace_search_users'),
    path('workspaces/<uuid:ws_id>/', views.workspace_detail, name='workspace_detail'),
    path('workspaces/<uuid:ws_id>/chat/', views.workspace_send_message, name='workspace_send_message'),
    path('workspaces/<uuid:ws_id>/poll/', views.workspace_poll_messages, name='workspace_poll_messages'),
    path('workspaces/<uuid:ws_id>/files/', views.workspace_upload_file, name='workspace_upload_file'),
    path('workspaces/<uuid:ws_id>/tasks/', views.workspace_add_task, name='workspace_add_task'),
    path('workspaces/<uuid:ws_id>/tasks/<uuid:task_id>/', views.workspace_update_task, name='workspace_update_task'),
    path('workspaces/<uuid:ws_id>/members/add/', views.workspace_add_member, name='workspace_add_member'),
    path('workspaces/<uuid:ws_id>/members/<int:user_id>/remove/', views.workspace_remove_member, name='workspace_remove_member'),
    path('workspaces/<uuid:ws_id>/leave/', views.workspace_leave, name='workspace_leave'),
    path('workspaces/<uuid:ws_id>/delete/', views.workspace_delete, name='workspace_delete'),
    path('workspaces/<uuid:ws_id>/call/join/', views.workspace_call_join, name='workspace_call_join'),
    path('workspaces/<uuid:ws_id>/call/leave/', views.workspace_call_leave, name='workspace_call_leave'),
    path('workspaces/<uuid:ws_id>/call/participants/', views.workspace_call_participants, name='workspace_call_participants'),
    # AI Manager
    path('workspaces/<uuid:ws_id>/ai/chat/', views.workspace_ai_chat, name='workspace_ai_chat'),
    path('workspaces/<uuid:ws_id>/ai/analyze/', views.workspace_ai_analyze, name='workspace_ai_analyze'),
    path('workspaces/<uuid:ws_id>/ai/health/', views.workspace_ai_health, name='workspace_ai_health'),
    path('workspaces/<uuid:ws_id>/ai/meeting/', views.workspace_ai_meeting, name='workspace_ai_meeting'),
    path('workspaces/<uuid:ws_id>/ai/autocomplete/', views.workspace_ai_autocomplete, name='workspace_ai_autocomplete'),

    # REST API
    path('api/', include(router.urls)),

    # Quick join from feed
    path('api/communities/<slug:slug>/quick-join/', views.quick_join_custom, name='quick_join_custom'),
    path('api/schools/<slug:slug>/quick-join/', views.quick_join_school, name='quick_join_school'),

    # Share post via DM
    path('api/share/conversations/', views.share_post_dm_list, name='share_dm_list'),
    path('api/posts/<uuid:post_id>/share/', views.share_post_send, name='share_post_send'),

    # Follow toggle
    path('api/follow-toggle/', views.follow_toggle, name='follow_toggle'),

    # Friend requests
    path('api/friends/request/<str:username>/', views.friend_request_send, name='friend_request_send'),
    path('api/friends/respond/<uuid:friendship_id>/', views.friend_request_respond, name='friend_request_respond'),
    path('api/friends/status/<str:username>/', views.friend_status, name='friend_status'),
    path('api/friends/pending/', views.pending_friend_requests, name='pending_friend_requests'),
    path('api/users/search/', views.search_users, name='search_users'),
    path('api/profile-stats/<str:username>/', views.profile_stats, name='profile_stats'),

    # Radar APIs (used by AI Hub)
    path('api/workspaces/list/', views.api_workspaces_list, name='api_workspaces_list'),
    path('api/posts/recent/', views.api_posts_recent, name='api_posts_recent'),
    path('api/communities/list/', views.api_communities_list, name='api_communities_list'),
]
