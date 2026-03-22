"""
DRF ViewSets for the community app.
All endpoints require authentication unless explicitly noted.
"""

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from community.models import (
    Block,
    Comment,
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
from community.permissions import (
    IsCommentAuthor,
    IsConversationParticipant,
    IsPostAuthorOrModerator,
)
from community.serializers import (
    BlockSerializer,
    CommentSerializer,
    CommunityMembershipSerializer,
    ConversationSerializer,
    CustomCommunitySerializer,
    FeedResponseSerializer,
    FollowSerializer,
    MessageSerializer,
    NotificationSerializer,
    PostSerializer,
    SchoolCommunitySerializer,
    SpaceSerializer,
)
from community.services.feed import get_personalized_feed


# ── School Community ──────────────────────────────────────────────────────────

class SchoolCommunityViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    List and retrieve official school communities.
    Join/leave via dedicated actions.
    """

    queryset = SchoolCommunity.objects.filter(is_active=True).order_by('name')
    serializer_class = SchoolCommunitySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']

    @action(detail=True, methods=['post'], url_path='join')
    def join(self, request, pk=None):
        """Join a school community."""
        community = self.get_object()
        membership, created = CommunityMembership.objects.get_or_create(
            user=request.user,
            community=community,
            defaults={'role': CommunityMembership.ROLE_MEMBER},
        )
        if not created:
            return Response(
                {'detail': 'Already a member.'}, status=status.HTTP_200_OK
            )
        serializer = CommunityMembershipSerializer(membership, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='leave')
    def leave(self, request, pk=None):
        """Leave a school community."""
        community = self.get_object()
        deleted, _ = CommunityMembership.objects.filter(
            user=request.user, community=community
        ).delete()
        if deleted:
            return Response({'detail': 'Left community.'}, status=status.HTTP_200_OK)
        return Response({'detail': 'Not a member.'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='members')
    def members(self, request, pk=None):
        """List members of a school community."""
        community = self.get_object()
        memberships = community.memberships.select_related('user').order_by('joined_at')
        serializer = CommunityMembershipSerializer(
            memberships, many=True, context={'request': request}
        )
        return Response(serializer.data)


# ── Custom Community ──────────────────────────────────────────────────────────

class CustomCommunityViewSet(viewsets.ModelViewSet):
    """CRUD for user-created communities."""

    serializer_class = CustomCommunitySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']

    def get_queryset(self):
        user = self.request.user
        # Public communities are visible to all; private only to members/creator
        return CustomCommunity.objects.filter(
            Q(privacy=CustomCommunity.PRIVACY_PUBLIC)
            | Q(creator=user)
        ).filter(is_active=True).order_by('-created_at')

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.creator != request.user and not request.user.is_staff:
            return Response(
                {'detail': 'Only the creator can delete this community.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)


# ── Post ──────────────────────────────────────────────────────────────────────

class PostViewSet(viewsets.ModelViewSet):
    """
    Create, list, retrieve, update, delete posts.
    Soft-delete on destroy. Membership enforced on create.
    """

    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated, IsPostAuthorOrModerator]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['content', 'category']
    ordering_fields = ['created_at', 'like_count', 'comment_count']

    def get_queryset(self):
        qs = (
            Post.objects.filter(is_deleted=False)
            .select_related('author', 'school_community', 'custom_community')
            .order_by('-created_at')
        )
        # Optional filter by community
        sc_id = self.request.query_params.get('school_community')
        cc_id = self.request.query_params.get('custom_community')
        if sc_id:
            qs = qs.filter(school_community_id=sc_id)
        if cc_id:
            qs = qs.filter(custom_community_id=cc_id)
        return qs

    def perform_create(self, serializer):
        """Validate membership before saving."""
        sc_id = self.request.data.get('school_community_id')
        if sc_id:
            is_member = CommunityMembership.objects.filter(
                user=self.request.user, community_id=sc_id
            ).exists()
            if not is_member:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('You must join this community before posting.')
        serializer.save(author=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """Soft delete."""
        post = self.get_object()
        post.is_deleted = True
        post.save(update_fields=['is_deleted'])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='like')
    def like(self, request, pk=None):
        """Toggle like on a post."""
        post = self.get_object()
        like, created = PostLike.objects.get_or_create(user=request.user, post=post)
        if not created:
            like.delete()
            post.refresh_from_db(fields=['like_count'])
            return Response({'liked': False, 'like_count': post.like_count})
        post.refresh_from_db(fields=['like_count'])
        return Response({'liked': True, 'like_count': post.like_count})

    @action(detail=True, methods=['get', 'post'], url_path='comments')
    def comments(self, request, pk=None):
        """List or create comments on a post."""
        post = self.get_object()
        if request.method == 'GET':
            qs = (
                Comment.objects.filter(post=post, parent=None)
                .select_related('author')
                .prefetch_related('replies__author')
                .order_by('created_at')
            )
            serializer = CommentSerializer(qs, many=True, context={'request': request})
            return Response(serializer.data)

        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        serializer = CommentSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(author=request.user, post=post)
        # comment_count is updated by signal
        return Response(CommentSerializer(comment, context={'request': request}).data, status=status.HTTP_201_CREATED)


# ── Comment ───────────────────────────────────────────────────────────────────

class CommentViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Update and delete individual comments."""

    queryset = Comment.objects.select_related('author').all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsCommentAuthor]


# ── Follow ────────────────────────────────────────────────────────────────────

class FollowViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Follow/unfollow users."""

    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Follow.objects.filter(follower=self.request.user).select_related('following')

    @action(detail=False, methods=['delete'], url_path='unfollow/(?P<user_id>[^/.]+)')
    def unfollow(self, request, user_id=None):
        deleted, _ = Follow.objects.filter(
            follower=request.user, following_id=user_id
        ).delete()
        if deleted:
            return Response({'detail': 'Unfollowed.'}, status=status.HTTP_200_OK)
        return Response({'detail': 'Not following.'}, status=status.HTTP_400_BAD_REQUEST)


# ── Conversation ──────────────────────────────────────────────────────────────

class ConversationViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """List and create DM conversations."""

    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Conversation.objects.filter(participants=self.request.user)
            .prefetch_related('participants')
            .order_by('-updated_at')
        )

    def get_permissions(self):
        if self.action == 'retrieve':
            return [IsAuthenticated(), IsConversationParticipant()]
        return super().get_permissions()

    @action(detail=True, methods=['get', 'post'], url_path='messages')
    def messages(self, request, pk=None):
        """List or send messages in a conversation."""
        conversation = self.get_object()

        # Verify participant
        if not conversation.participants.filter(pk=request.user.pk).exists():
            return Response(
                {'detail': 'Not a participant.'}, status=status.HTTP_403_FORBIDDEN
            )

        if request.method == 'GET':
            msgs = conversation.messages.select_related('sender').order_by('created_at')
            # Mark unread as read
            msgs.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
            serializer = MessageSerializer(msgs, many=True, context={'request': request})
            return Response(serializer.data)

        serializer = MessageSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        msg = serializer.save(sender=request.user, conversation=conversation)
        # Bump conversation updated_at for ordering
        Conversation.objects.filter(pk=conversation.pk).update(
            updated_at=msg.created_at
        )
        return Response(
            MessageSerializer(msg, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


# ── Notification ──────────────────────────────────────────────────────────────

class NotificationViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """List and mark notifications as read."""

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Notification.objects.filter(recipient=self.request.user)
            .select_related('actor', 'post', 'comment')
            .order_by('-created_at')
        )

    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(
            is_read=True
        )
        return Response({'detail': 'All notifications marked as read.'})

    @action(detail=True, methods=['post'], url_path='read')
    def mark_read(self, request, pk=None):
        notif = get_object_or_404(Notification, pk=pk, recipient=request.user)
        notif.is_read = True
        notif.save(update_fields=['is_read'])
        return Response({'detail': 'Marked as read.'})


# ── Feed ──────────────────────────────────────────────────────────────────────

class FeedViewSet(viewsets.ViewSet):
    """Personalized feed endpoint."""

    permission_classes = [IsAuthenticated]

    def list(self, request):
        limit = request.query_params.get('limit', 20)
        cursor = request.query_params.get('cursor', None)
        result = get_personalized_feed(user=request.user, limit=limit, cursor=cursor)
        serializer = FeedResponseSerializer(result, context={'request': request})
        return Response(serializer.data)


# ── Space ─────────────────────────────────────────────────────────────────────

class SpaceViewSet(viewsets.ModelViewSet):
    """Voice/video room management."""

    serializer_class = SpaceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'description']

    def get_queryset(self):
        return Space.objects.select_related('host').order_by('-created_at')

    @action(detail=True, methods=['post'], url_path='end')
    def end_space(self, request, pk=None):
        from django.utils import timezone
        space = self.get_object()
        if space.host != request.user:
            return Response(
                {'detail': 'Only the host can end this space.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        space.is_live = False
        space.ended_at = timezone.now()
        space.save(update_fields=['is_live', 'ended_at'])
        return Response({'detail': 'Space ended.'})


# ── Block ─────────────────────────────────────────────────────────────────────

class BlockViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Block/unblock users."""

    serializer_class = BlockSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Block.objects.filter(blocker=self.request.user).select_related('blocked')

    @action(detail=False, methods=['delete'], url_path='unblock/(?P<user_id>[^/.]+)')
    def unblock(self, request, user_id=None):
        deleted, _ = Block.objects.filter(
            blocker=request.user, blocked_id=user_id
        ).delete()
        if deleted:
            return Response({'detail': 'Unblocked.'})
        return Response({'detail': 'Not blocked.'}, status=status.HTTP_400_BAD_REQUEST)
