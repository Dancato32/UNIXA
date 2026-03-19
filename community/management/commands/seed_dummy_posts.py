"""
Management command: seed dummy posts for the community feed.
Usage: python manage.py seed_dummy_posts
"""
import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from community.models import SchoolCommunity, CustomCommunity, Post, CommunityMembership

User = get_user_model()

DUMMY_POSTS = [
    {
        "author": "alex_nexa",
        "community": "school",
        "content": "Just finished my final exams! 🎉 Three years of hard work finally paying off. To everyone still grinding — you've got this. The late nights are worth it.",
        "category": "Academics",
    },
    {
        "author": "priya_dev",
        "community": "school",
        "content": "Hot take: group projects are actually great preparation for real-world work. Fight me. 😂\n\nSeriously though, learning to coordinate with different personalities is a skill nobody teaches you explicitly.",
        "category": "Campus Life",
    },
    {
        "author": "kwame_builds",
        "community": "school",
        "content": "Our robotics team just won the regional competition! 🤖🏆 We've been building this bot for 6 months. Huge shoutout to everyone who stayed in the lab until 2am with us.",
        "category": "Events",
    },
    {
        "author": "sara_writes",
        "community": "school",
        "content": "Reminder that the library extended hours start this week — open until midnight every day through finals. Stock up on snacks, grab a study spot early. Good luck everyone! 📚",
        "category": "Announcements",
    },
    {
        "author": "alex_nexa",
        "community": "school",
        "content": "Anyone else feel like the campus WiFi gets worse exactly when you need it most? Trying to submit an assignment at 11:58pm and the connection just... disappears. 😤",
        "category": "Campus Life",
    },
    {
        "author": "priya_dev",
        "community": "school",
        "content": "PSA: The new computer science elective on machine learning is actually incredible. Prof. Mensah explains everything from first principles. If you can still add it, do it.",
        "category": "Academics",
    },
    {
        "author": "kwame_builds",
        "community": "school",
        "content": "Hosting a free Python workshop this Saturday at 10am in Block C, Room 204. Absolute beginners welcome. We'll cover basics, build a small project, and have fun. DM me to register!",
        "category": "Events",
    },
    {
        "author": "sara_writes",
        "community": "school",
        "content": "The campus food court just added a new jollof rice spot and honestly it might be the best thing that's happened this semester. The queue at lunch is real though 😅",
        "category": "Campus Life",
    },
    {
        "author": "alex_nexa",
        "community": "school",
        "content": "Internship season is here. A few tips from someone who just went through it:\n\n1. Apply early — most deadlines are earlier than you think\n2. Tailor your CV for each role\n3. Your GPA matters less than your projects\n4. Follow up after interviews\n\nGood luck! 🚀",
        "category": "Career",
    },
    {
        "author": "priya_dev",
        "community": "school",
        "content": "Shoutout to the student union for organizing the mental health awareness week. These conversations matter. Check in on your friends, not just during exams. 💙",
        "category": "Wellness",
    },
    {
        "author": "kwame_builds",
        "community": "school",
        "content": "The engineering faculty just got new 3D printers! Open access for all students with a valid student ID. Book your slot through the faculty portal. This is huge for our projects.",
        "category": "Academics",
    },
    {
        "author": "sara_writes",
        "community": "school",
        "content": "Writing tip of the day: your first draft is supposed to be bad. Stop trying to write perfectly and just get the ideas down. You can't edit a blank page. ✍️",
        "category": "Academics",
    },
    {
        "author": "alex_nexa",
        "community": "school",
        "content": "Campus football tournament starts next week! All departments are fielding teams. Come support your department — matches are at the main field, 4pm daily. 🏆⚽",
        "category": "Sports",
    },
    {
        "author": "priya_dev",
        "community": "school",
        "content": "Just discovered you can access IEEE Xplore, ACM Digital Library, and JSTOR for free through the library portal. Game changer for research. Why did nobody tell me this in first year?!",
        "category": "Academics",
    },
    {
        "author": "kwame_builds",
        "community": "school",
        "content": "Reminder: the scholarship application deadline is in 2 weeks. Don't sleep on it — there are several awards that go unclaimed every year simply because students don't apply. Check the financial aid office website.",
        "category": "Announcements",
    },
]

DUMMY_USERS = [
    {"username": "alex_nexa", "email": "alex@nexa.edu", "password": "nexapass123"},
    {"username": "priya_dev", "email": "priya@nexa.edu", "password": "nexapass123"},
    {"username": "kwame_builds", "email": "kwame@nexa.edu", "password": "nexapass123"},
    {"username": "sara_writes", "email": "sara@nexa.edu", "password": "nexapass123"},
]


class Command(BaseCommand):
    help = 'Seed dummy posts and users for the community feed'

    def handle(self, *args, **options):
        # Create dummy users
        users = {}
        for u in DUMMY_USERS:
            user, created = User.objects.get_or_create(
                username=u['username'],
                defaults={'email': u['email']}
            )
            if created:
                user.set_password(u['password'])
                user.save()
                self.stdout.write(f'  Created user: {u["username"]}')
            users[u['username']] = user

        # Get or create a default school community
        school = SchoolCommunity.objects.filter(is_active=True).first()
        if not school:
            school = SchoolCommunity.objects.create(
                name='NEXA University',
                description='The official NEXA University community.',
                verified=True,
                is_active=True,
            )
            self.stdout.write(f'  Created school: {school.name}')

        # Join all dummy users to the school
        for user in users.values():
            CommunityMembership.objects.get_or_create(
                user=user,
                community=school,
                defaults={'role': CommunityMembership.ROLE_MEMBER}
            )

        # Create posts
        created_count = 0
        for post_data in DUMMY_POSTS:
            author = users.get(post_data['author'])
            if not author:
                continue
            # Avoid duplicates
            if Post.objects.filter(author=author, content=post_data['content']).exists():
                continue
            Post.objects.create(
                author=author,
                school_community=school,
                content=post_data['content'],
                category=post_data.get('category', ''),
                like_count=random.randint(3, 120),
                comment_count=random.randint(0, 25),
            )
            created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done. Created {created_count} dummy posts in "{school.name}".'
        ))
