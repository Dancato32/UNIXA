"""
Custom DRF permissions for the community app.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS

from community.models import CommunityMembership, CustomCommunity


class IsAuthenticatedOrReadOnly(BasePermission):
    """Allow read to anyone; write requires authentication."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated


class IsCommunityMember(BasePermission):
    """
    Object-level: user must be a member of the community the post belongs to.
    Used on Post creation — checked in the viewset, not here directly.
    """

    message = 'You must be a member of this community to post.'

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsPostAuthorOrModerator(BasePermission):
    """
    Allow edit/delete only to the post author, community mods, or admins.
    Safe methods are always allowed.
    """

    message = 'Only the author or a moderator can modify this post.'

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        # Author can always edit/delete their own post
        if obj.author == request.user:
            return True

        # Check if user is mod/admin in the relevant community
        community = obj.school_community
        if community:
            return CommunityMembership.objects.filter(
                user=request.user,
                community=community,
                role__in=[CommunityMembership.ROLE_MOD, CommunityMembership.ROLE_ADMIN],
            ).exists()

        return False


class IsCommentAuthor(BasePermission):
    """Only the comment author can edit or delete."""

    message = 'Only the comment author can modify this comment.'

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user


class CanAccessPrivateCommunity(BasePermission):
    """
    For CustomCommunity: private communities require membership to view content.
    """

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, CustomCommunity):
            if obj.privacy == CustomCommunity.PRIVACY_PUBLIC:
                return True
            # Private: must be a member (checked via post's custom_community)
            return obj.members.filter(user=request.user).exists()
        return True


class IsConversationParticipant(BasePermission):
    """Only conversation participants can read or send messages."""

    message = 'You are not a participant in this conversation.'

    def has_object_permission(self, request, view, obj):
        return obj.participants.filter(pk=request.user.pk).exists()
