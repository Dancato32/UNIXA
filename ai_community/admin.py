from django.contrib import admin
from ai_community.models import UserAIProfile, AIMatch, StartupTeam, StartupTeamMember, AIOpportunity, ExpertBadge

@admin.register(UserAIProfile)
class UserAIProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'skills', 'startup_interest', 'updated_at']
    search_fields = ['user__username', 'skills', 'interests']

@admin.register(StartupTeam)
class StartupTeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'founder', 'industry', 'stage', 'status', 'created_at']
    list_filter = ['status', 'industry']
    search_fields = ['name', 'idea', 'founder__username']

@admin.register(StartupTeamMember)
class StartupTeamMemberAdmin(admin.ModelAdmin):
    list_display = ['team', 'user', 'role', 'status', 'joined_at']
    list_filter = ['status']

@admin.register(AIOpportunity)
class AIOpportunityAdmin(admin.ModelAdmin):
    list_display = ['title', 'opp_type', 'is_active', 'created_at']
    list_filter = ['opp_type', 'is_active']
    search_fields = ['title', 'description']

@admin.register(ExpertBadge)
class ExpertBadgeAdmin(admin.ModelAdmin):
    list_display = ['user', 'label', 'subject', 'score', 'awarded_at']

@admin.register(AIMatch)
class AIMatchAdmin(admin.ModelAdmin):
    list_display = ['user', 'matched_user', 'match_type', 'score']
    list_filter = ['match_type']
