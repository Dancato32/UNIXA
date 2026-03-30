"""
DRF serializers for the community app.
Designed to avoid N+1 queries — use select_related/prefetch_related in viewsets.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from community.models import (
    Block,
    Comment,
    CommentLike,
    CommunityMembership,
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

User = get_user_model()


# ── Minimal user representation ───────────────────────────────────────────────

class UserMinimalSerializer(serializers.ModelSerializer):
    """Lightweight user info embedded in other serializers."""

    class Meta:
        model = User
        fields = ['id', 'username', 'profile_picture']


# ── School Community ──────────────────────────────────────────────────────────

class SchoolCommunitySerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()
    is_member = serializers.SerializerMethodField()

    class Meta:
        model = SchoolCommunity
        fields = [
            'id', 'name', 'slug', 'description', 'logo', 'banner',
            'verified', 'is_active', 'member_count', 'is_member', 'created_at',
        ]
        read_only_fields = ['id', 'verified', 'created_at', 'slug']

    def get_member_count(self, obj):
        return obj.memberships.count()

    def get_is_member(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.memberships.filter(user=request.user).exists()
        return False


# ── Community Membership ──────────────────────────────────────────────────────

class CommunityMembershipSerializer(serializers.ModelSerializer):
    user = UserMinimalSerializer(read_only=True)
    community = SchoolCommunitySerializer(read_only=True)

    class Meta:
        model = CommunityMembership
        fields = ['id', 'user', 'community', 'role', 'joined_at', 'notifications_enabled']
        read_only_fields = ['id', 'joined_at', 'user', 'community']


# ── Custom Community ──────────────────────────────────────────────────────────

class CustomCommunitySerializer(serializers.ModelSerializer):
    creator = UserMinimalSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = CustomCommunity
        fields = [
            'id', 'name', 'slug', 'description', 'creator', 'privacy',
            'logo', 'banner', 'rules', 'is_active', 'member_count', 'created_at',
        ]
        read_only_fields = ['id', 'slug', 'creator', 'created_at']

    def get_member_count(self, obj):
        # CustomCommunity doesn't have memberships model yet — return 0 safely
        return 0

    def create(self, validated_data):
        validated_data['creator'] = self.context['request'].user
        return super().create(validated_data)


# ── Post ──────────────────────────────────────────────────────────────────────

class PostSerializer(serializers.ModelSerializer):
    author = UserMinimalSerializer(read_only=True)
    school_community = SchoolCommunitySerializer(read_only=True)
    school_community_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    custom_community_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'author', 'school_community', 'school_community_id',
            'custom_community_id', 'content', 'media', 'media_type',
            'category', 'created_at', 'updated_at',
            'like_count', 'comment_count', 'share_count', 'is_liked',
        ]
        read_only_fields = [
            'id', 'author', 'created_at', 'updated_at',
            'like_count', 'comment_count', 'share_count',
        ]

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return PostLike.objects.filter(user=request.user, post=obj).exists()
        return False

    def validate(self, data):
        sc = data.get('school_community_id')
        cc = data.get('custom_community_id')
        feed_only = data.get('feed_only', False)
        # Allow feed-only posts (no community required)
        if not sc and not cc and not feed_only:
            # Still allow — the viewset/view will set feed_only=True for API posts
            pass
        if sc and cc:
            raise serializers.ValidationError(
                'A post cannot belong to both community types simultaneously.'
            )
        return data

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        sc_id = validated_data.pop('school_community_id', None)
        cc_id = validated_data.pop('custom_community_id', None)
        if sc_id:
            validated_data['school_community_id'] = sc_id
        if cc_id:
            validated_data['custom_community_id'] = cc_id
        return super().create(validated_data)


# ── Comment ───────────────────────────────────────────────────────────────────

class CommentSerializer(serializers.ModelSerializer):
    author = UserMinimalSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    reply_count = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id', 'post', 'author', 'parent', 'content',
            'created_at', 'updated_at', 'like_count', 'replies',
            'is_liked', 'reply_count',
        ]
        read_only_fields = ['id', 'post', 'author', 'created_at', 'updated_at', 'like_count', 'is_liked', 'reply_count']

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and getattr(request.user, 'is_authenticated', False):
            return CommentLike.objects.filter(user=request.user, comment=obj).exists()
        return False

    def get_reply_count(self, obj):
        return obj.replies.count()

    def get_replies(self, obj):
        # Only one level deep to avoid deep recursion
        if obj.parent is None:
            return CommentSerializer(
                obj.replies.all(), many=True, context=self.context
            ).data
        return []

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


# ── Follow ────────────────────────────────────────────────────────────────────

class FollowSerializer(serializers.ModelSerializer):
    follower = UserMinimalSerializer(read_only=True)
    following = UserMinimalSerializer(read_only=True)
    following_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Follow
        fields = ['id', 'follower', 'following', 'following_id', 'created_at']
        read_only_fields = ['id', 'follower', 'created_at']

    def validate_following_id(self, value):
        request = self.context['request']
        if value == request.user.pk:
            raise serializers.ValidationError('You cannot follow yourself.')
        if not User.objects.filter(pk=value).exists():
            raise serializers.ValidationError('User not found.')
        return value

    def create(self, validated_data):
        validated_data['follower'] = self.context['request'].user
        return super().create(validated_data)


# ── Message ───────────────────────────────────────────────────────────────────

class MessageSerializer(serializers.ModelSerializer):
    sender = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'sender', 'content', 'media',
            'message_type', 'is_read', 'created_at',
        ]
        read_only_fields = ['id', 'sender', 'is_read', 'created_at']

    def create(self, validated_data):
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)


# ── Conversation ──────────────────────────────────────────────────────────────

class ConversationSerializer(serializers.ModelSerializer):
    participants = UserMinimalSerializer(many=True, read_only=True)
    participant_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True
    )
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id', 'participants', 'participant_ids',
            'is_group', 'created_at', 'updated_at', 'last_message',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_last_message(self, obj):
        msg = obj.messages.order_by('-created_at').first()
        if msg:
            return MessageSerializer(msg, context=self.context).data
        return None

    def create(self, validated_data):
        participant_ids = validated_data.pop('participant_ids', [])
        conversation = Conversation.objects.create(
            is_group=validated_data.get('is_group', False)
        )
        # Always include the requesting user
        all_ids = set(participant_ids) | {self.context['request'].user.pk}
        users = User.objects.filter(pk__in=all_ids)
        conversation.participants.set(users)
        return conversation


# ── Notification ──────────────────────────────────────────────────────────────

class NotificationSerializer(serializers.ModelSerializer):
    actor = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'actor', 'type', 'post', 'comment', 'is_read', 'created_at',
        ]
        read_only_fields = fields


# ── Space ─────────────────────────────────────────────────────────────────────

class SpaceSerializer(serializers.ModelSerializer):
    host = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Space
        fields = [
            'id', 'host', 'title', 'description', 'school_community',
            'custom_community', 'is_live', 'allow_video',
            'max_participants', 'created_at', 'ended_at',
        ]
        read_only_fields = ['id', 'host', 'created_at']

    def create(self, validated_data):
        validated_data['host'] = self.context['request'].user
        return super().create(validated_data)


# ── Block ─────────────────────────────────────────────────────────────────────

class BlockSerializer(serializers.ModelSerializer):
    blocker = UserMinimalSerializer(read_only=True)
    blocked = UserMinimalSerializer(read_only=True)
    blocked_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Block
        fields = ['id', 'blocker', 'blocked', 'blocked_id', 'created_at']
        read_only_fields = ['id', 'blocker', 'created_at']

    def validate_blocked_id(self, value):
        request = self.context['request']
        if value == request.user.pk:
            raise serializers.ValidationError('You cannot block yourself.')
        return value

    def create(self, validated_data):
        validated_data['blocker'] = self.context['request'].user
        return super().create(validated_data)


# ── Feed ──────────────────────────────────────────────────────────────────────

class FeedResponseSerializer(serializers.Serializer):
    """Wraps the feed service response for the API."""
    posts = PostSerializer(many=True)
    next_cursor = serializers.CharField(allow_null=True)
    has_more = serializers.BooleanField()
