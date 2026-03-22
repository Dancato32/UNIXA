from django.contrib import admin
from campus.models import (
    SkillListing, SkillDeal,
    Confession, ConfessionReply,
    Startup, StartupMember, StartupUpdate, StartupFollow,
    PulseActivity, PulseJoin,
    VoiceRoom, VoiceRoomParticipant,
    HelpBeacon, UserReputation,
)

@admin.register(SkillListing)
class SkillListingAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'listing_type', 'skill_tag', 'status', 'urgency', 'created_at']
    list_filter = ['listing_type', 'skill_tag', 'status', 'urgency']
    search_fields = ['title', 'user__username']

@admin.register(SkillDeal)
class SkillDealAdmin(admin.ModelAdmin):
    list_display = ['initiator', 'receiver', 'listing', 'status', 'created_at']
    list_filter = ['status']

@admin.register(Confession)
class ConfessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'category', 'status', 'is_crisis', 'upvote_count', 'reply_count', 'created_at']
    list_filter = ['category', 'status', 'is_crisis']
    # author intentionally not shown in list to reinforce anonymity culture

@admin.register(ConfessionReply)
class ConfessionReplyAdmin(admin.ModelAdmin):
    list_display = ['confession', 'author', 'is_anonymous', 'is_helpful', 'is_flagged', 'created_at']
    list_filter = ['is_anonymous', 'is_helpful', 'is_flagged']

@admin.register(Startup)
class StartupAdmin(admin.ModelAdmin):
    list_display = ['name', 'founder', 'stage', 'is_recruiting', 'follower_count', 'created_at']
    list_filter = ['stage', 'is_recruiting', 'is_active']
    search_fields = ['name', 'founder__username']

@admin.register(StartupMember)
class StartupMemberAdmin(admin.ModelAdmin):
    list_display = ['startup', 'user', 'role', 'status', 'joined_at']
    list_filter = ['role', 'status']

@admin.register(StartupUpdate)
class StartupUpdateAdmin(admin.ModelAdmin):
    list_display = ['startup', 'author', 'milestone', 'created_at']

@admin.register(PulseActivity)
class PulseActivityAdmin(admin.ModelAdmin):
    list_display = ['title', 'activity_type', 'host', 'participant_count', 'expires_at', 'is_private']
    list_filter = ['activity_type', 'is_private']
    search_fields = ['title', 'host__username']

@admin.register(VoiceRoom)
class VoiceRoomAdmin(admin.ModelAdmin):
    list_display = ['topic', 'host', 'status', 'participant_count', 'created_at', 'ended_at']
    list_filter = ['status']

@admin.register(HelpBeacon)
class HelpBeaconAdmin(admin.ModelAdmin):
    list_display = ['title', 'requester', 'category', 'urgency', 'status', 'helper', 'created_at']
    list_filter = ['category', 'urgency', 'status']
    search_fields = ['title', 'requester__username']

@admin.register(UserReputation)
class UserReputationAdmin(admin.ModelAdmin):
    list_display = ['user', 'score', 'deals_completed', 'help_given', 'avg_rating']
    ordering = ['-score']
