"""
Data migration: seed official Ghanaian school communities.

Uses get_or_create so it is:
  - Safe to run multiple times (idempotent)
  - Safe on empty or populated databases
  - Reversible (reverse_func removes only the seeded records)
"""

from django.db import migrations
from django.utils.text import slugify

OFFICIAL_SCHOOLS = [
    {
        'name': 'University of Ghana',
        'description': (
            'The University of Ghana (UG) is the oldest and largest university in Ghana, '
            'located at Legon, Accra. Founded in 1948.'
        ),
    },
    {
        'name': 'Kwame Nkrumah University of Science and Technology',
        'description': (
            'KNUST is a public research university located in Kumasi, Ghana. '
            'It is the premier science and technology university in Ghana.'
        ),
    },
    {
        'name': 'Ashesi University',
        'description': (
            'Ashesi University is a private liberal arts university in Berekuso, Ghana, '
            'focused on ethical leadership and innovation.'
        ),
    },
    {
        'name': 'University of Cape Coast',
        'description': (
            'UCC is a public research university located in Cape Coast, Ghana. '
            'Known for education and humanities programmes.'
        ),
    },
    {
        'name': 'University of Professional Studies Accra',
        'description': (
            'UPSA is a public university in Accra, Ghana, specialising in '
            'business, management, and professional studies.'
        ),
    },
]


def seed_communities(apps, schema_editor):
    """Create official school communities if they do not already exist."""
    SchoolCommunity = apps.get_model('community', 'SchoolCommunity')
    for school in OFFICIAL_SCHOOLS:
        SchoolCommunity.objects.get_or_create(
            name=school['name'],
            defaults={
                'slug': slugify(school['name']),
                'description': school['description'],
                'verified': True,
                'is_active': True,
            },
        )


def remove_seeded_communities(apps, schema_editor):
    """Reverse: remove only the communities seeded by this migration."""
    SchoolCommunity = apps.get_model('community', 'SchoolCommunity')
    names = [s['name'] for s in OFFICIAL_SCHOOLS]
    SchoolCommunity.objects.filter(name__in=names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_communities, reverse_code=remove_seeded_communities),
    ]
