"""
Admin configuration for the community app.
All models registered with search, filters, and useful inlines.
"""

from django.contrib import admin

from community.models import (
    Block,
    Comment,
    CommentLike,
    CommunityMembership,
    CommunityProfile,
    Conversation,
    CustomCommunity,
    Follow,
    Message,
    Notification,
    Post,
    PostLike,
    SchoolCommunity,
    Space,
)


# ── Inlines ───────────────────────────────────────────────────────────────────

class CommunityMembershipInline(admin.TabularInline):
    model = CommunityMembership
    extra = 0
    readonly_fields = ('joined_at',)
    fields = ('user', 'role', 'notifications_enabled', 'joined_at')


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('created_at',)
    fields = ('sender', 'content', 'message_type', 'is_read', 'created_at')


# ── School Community ──────────────────────────────────────────────────────────

@admin.register(SchoolCommunity)
class SchoolCommunityAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'verified', 'is_active', 'member_count', 'created_at')
    list_filter = ('verified', 'is_active')
    search_fields = ('name', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [CommunityMembershipInline]
    actions = ['activate_communities', 'deactivate_communities']

    def member_count(self, obj):
        return obj.memberships.count()
    member_count.short_description = 'Members'

    def activate_communities(self, request, queryset):
        queryset.update(is_active=True)
    activate_communities.short_description = 'Activate selected communities'

    def deactivate_communities(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_communities.short_description = 'Deactivate selected communities'


# ── Community Membership ──────────────────────────────────────────────────────

@admin.register(CommunityMembership)
class CommunityMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'community', 'role', 'joined_at', 'notifications_enabled')
    list_filter = ('role', 'notifications_enabled')
    search_fields = ('user__username', 'community__name')
    readonly_fields = ('id', 'joined_at')
    raw_id_fields = ('user', 'community')


# ── Custom Community ──────────────────────────────────────────────────────────

@admin.register(CustomCommunity)
class CustomCommunityAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'creator', 'privacy', 'is_active', 'created_at')
    list_filter = ('privacy', 'is_active')
    search_fields = ('name', 'description', 'creator__username')
    readonly_fields = ('id', 'created_at')
    raw_id_fields = ('creator',)


# ── Post ──────────────────────────────────────────────────────────────────────

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'author', 'school_community', 'custom_community',
        'category', 'like_count', 'comment_count', 'is_deleted', 'created_at',
    )
    list_filter = ('is_deleted', 'media_type', 'category')
    search_fields = ('content', 'author__username', 'category')
    readonly_fields = ('id', 'created_at', 'updated_at', 'like_count', 'comment_count', 'share_count')
    raw_id_fields = ('author', 'school_community', 'custom_community')
    actions = ['soft_delete_posts', 'restore_posts']

    def soft_delete_posts(self, request, queryset):
        queryset.update(is_deleted=True)
    soft_delete_posts.short_description = 'Soft-delete selected posts'

    def restore_posts(self, request, queryset):
        queryset.update(is_deleted=False)
    restore_posts.short_description = 'Restore selected posts'


# ── Post Like ─────────────────────────────────────────────────────────────────

@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')
    search_fields = ('user__username',)
    readonly_fields = ('id', 'created_at')
    raw_id_fields = ('user', 'post')


@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'comment', 'created_at')
    search_fields = ('user__username',)
    readonly_fields = ('id', 'created_at')
    raw_id_fields = ('user', 'comment')


# ── Comment ───────────────────────────────────────────────────────────────────

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'post', 'parent', 'like_count', 'created_at')
    search_fields = ('content', 'author__username')
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('author', 'post', 'parent')


# ── Follow ────────────────────────────────────────────────────────────────────

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'following', 'created_at')
    search_fields = ('follower__username', 'following__username')
    readonly_fields = ('id', 'created_at')
    raw_id_fields = ('follower', 'following')


# ── Conversation ──────────────────────────────────────────────────────────────

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'is_group', 'participant_list', 'created_at', 'updated_at')
    list_filter = ('is_group',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = [MessageInline]

    def participant_list(self, obj):
        return ', '.join(obj.participants.values_list('username', flat=True)[:5])
    participant_list.short_description = 'Participants'


# ── Message ───────────────────────────────────────────────────────────────────

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'conversation', 'message_type', 'is_read', 'created_at')
    list_filter = ('message_type', 'is_read')
    search_fields = ('content', 'sender__username')
    readonly_fields = ('id', 'created_at')
    raw_id_fields = ('sender', 'conversation')


# ── Space ─────────────────────────────────────────────────────────────────────

@admin.register(Space)
class SpaceAdmin(admin.ModelAdmin):
    list_display = ('title', 'host', 'is_live', 'allow_video', 'max_participants', 'created_at')
    list_filter = ('is_live', 'allow_video')
    search_fields = ('title', 'host__username')
    readonly_fields = ('id', 'created_at', 'ended_at')
    raw_id_fields = ('host',)


# ── Notification ──────────────────────────────────────────────────────────────

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'actor', 'type', 'is_read', 'created_at')
    list_filter = ('type', 'is_read')
    search_fields = ('recipient__username', 'actor__username')
    readonly_fields = ('id', 'created_at')
    raw_id_fields = ('recipient', 'actor', 'post', 'comment')


# ── Block ─────────────────────────────────────────────────────────────────────

@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ('blocker', 'blocked', 'created_at')
    search_fields = ('blocker__username', 'blocked__username')
    readonly_fields = ('id', 'created_at')
    raw_id_fields = ('blocker', 'blocked')


@admin.register(CommunityProfile)
class CommunityProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'updated_at')
    search_fields = ('user__username',)
    raw_id_fields = ('user',)
