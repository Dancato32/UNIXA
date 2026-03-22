from django.urls import path
from campus import views

app_name = 'campus'

urlpatterns = [
    # ── Live Campus Hub ──────────────────────────────────────────────────────
    path('', views.live_campus, name='live_campus'),

    # ── Skill Marketplace ────────────────────────────────────────────────────
    path('skills/', views.skill_marketplace, name='skill_marketplace'),
    path('skills/create/', views.skill_listing_create, name='skill_listing_create'),
    path('skills/<uuid:listing_id>/deal/', views.skill_deal_propose, name='skill_deal_propose'),
    path('skills/deals/<uuid:deal_id>/respond/', views.skill_deal_respond, name='skill_deal_respond'),
    path('skills/deals/<uuid:deal_id>/rate/', views.skill_deal_rate, name='skill_deal_rate'),

    # ── Confession Feed ──────────────────────────────────────────────────────
    path('confessions/', views.confession_feed, name='confession_feed'),
    path('confessions/create/', views.confession_create, name='confession_create'),
    path('confessions/<uuid:confession_id>/upvote/', views.confession_upvote, name='confession_upvote'),
    path('confessions/<uuid:confession_id>/reply/', views.confession_reply_create, name='confession_reply_create'),
    path('confessions/replies/<uuid:reply_id>/helpful/', views.confession_mark_helpful, name='confession_mark_helpful'),

    # ── Startup Command Center ───────────────────────────────────────────────
    path('startups/', views.startup_list, name='startup_list'),
    path('startups/create/', views.startup_create, name='startup_create'),
    path('startups/<uuid:startup_id>/', views.startup_detail, name='startup_detail'),
    path('startups/<uuid:startup_id>/follow/', views.startup_follow_toggle, name='startup_follow_toggle'),
    path('startups/<uuid:startup_id>/update/', views.startup_post_update, name='startup_post_update'),
    path('startups/<uuid:startup_id>/apply/', views.startup_apply, name='startup_apply'),
    path('startups/<uuid:startup_id>/support/', views.startup_support_interest, name='startup_support_interest'),

    # ── Campus Pulse ─────────────────────────────────────────────────────────
    path('pulse/', views.pulse_feed, name='pulse_feed'),
    path('pulse/create/', views.pulse_create, name='pulse_create'),
    path('pulse/<uuid:activity_id>/join/', views.pulse_join, name='pulse_join'),

    # ── Voice Rooms ──────────────────────────────────────────────────────────
    path('voice/', views.voice_rooms, name='voice_rooms'),
    path('voice/create/', views.voice_room_create, name='voice_room_create'),
    path('voice/<uuid:room_id>/join/', views.voice_room_join, name='voice_room_join'),
    path('voice/<uuid:room_id>/leave/', views.voice_room_leave, name='voice_room_leave'),
    path('voice/<uuid:room_id>/close/', views.voice_room_close, name='voice_room_close'),
    path('voice/<uuid:room_id>/participants/', views.voice_room_participants, name='voice_room_participants'),

    # ── Help Beacons ─────────────────────────────────────────────────────────
    path('help/', views.help_beacon_list, name='help_beacon_list'),
    path('help/create/', views.help_beacon_create, name='help_beacon_create'),
    path('help/<uuid:beacon_id>/claim/', views.help_beacon_claim, name='help_beacon_claim'),
    path('help/<uuid:beacon_id>/resolve/', views.help_beacon_resolve, name='help_beacon_resolve'),
]
