"""
Data migration: seed all Ghana universities into SchoolCommunity.
Idempotent — uses get_or_create so safe to run multiple times.
"""

from django.db import migrations
from django.utils.text import slugify

UNIVERSITIES = [
    # Traditional / Comprehensive
    ('University of Ghana', 'The oldest and largest university in Ghana, located at Legon, Accra. Founded in 1948.'),
    ('Kwame Nkrumah University of Science and Technology', 'Premier science and technology university in Ghana, located in Kumasi.'),
    ('University of Cape Coast', 'Public research university in Cape Coast, known for education and humanities programmes.'),
    ('University of Education, Winneba', 'Public university in Winneba focused on teacher education and professional development.'),
    ('University for Development Studies', 'Public university with campuses across northern Ghana, focused on development-oriented education.'),
    ('University of Mines and Technology', 'Specialised university in Tarkwa focused on mining, engineering and technology.'),
    ('University of Health and Allied Sciences', 'Public health-focused university located in Ho, Volta Region.'),
    ('University of Energy and Natural Resources', 'Public university in Sunyani focused on energy and natural resource management.'),
    ('University of Environment and Sustainable Development', 'Public university in Somanya focused on environmental and sustainable development studies.'),
    # Technical Universities
    ('Accra Technical University', 'Technical university in Accra offering applied science and technology programmes.'),
    ('Kumasi Technical University', 'Technical university in Kumasi offering engineering and applied science programmes.'),
    ('Cape Coast Technical University', 'Technical university in Cape Coast offering vocational and technical education.'),
    ('Takoradi Technical University', 'Technical university in Takoradi with a focus on engineering and maritime studies.'),
    ('Ho Technical University', 'Technical university in Ho, Volta Region, offering applied technical programmes.'),
    ('Koforidua Technical University', 'Technical university in Koforidua offering technology and business programmes.'),
    ('Tamale Technical University', 'Technical university in Tamale serving the northern regions of Ghana.'),
    ('Bolgatanga Technical University', 'Technical university in Bolgatanga serving the Upper East Region.'),
    # Private Universities
    ('Ashesi University', 'Private liberal arts university in Berekuso focused on ethical leadership and innovation.'),
    ('Central University', 'Private Christian university in Accra offering business, law and social sciences.'),
    ('Valley View University', 'Seventh-day Adventist university in Oyibi, Accra, offering diverse undergraduate programmes.'),
    ('Ghana Christian University College', 'Private Christian university college in Accra offering theology and business programmes.'),
    ('Methodist University Ghana', 'Private Methodist university in Accra offering business, arts and social sciences.'),
    ('Presbyterian University Ghana', 'Private Presbyterian university offering programmes in business, science and theology.'),
    ('Islamic University College Ghana', 'Private Islamic university in Accra offering Islamic studies and general education.'),
    ('Catholic University College of Ghana', 'Private Catholic university in Fiapre, Sunyani, offering diverse academic programmes.'),
    ('Pentecost University', 'Private Pentecostal university in Accra offering business, IT and social sciences.'),
    ('Garden City University College', 'Private university college in Kumasi offering business and technology programmes.'),
    ('Lancaster University Ghana', 'International branch campus of Lancaster University UK, located in Accra.'),
    ('Academic City University College', 'Private technology-focused university in Accra with strong industry partnerships.'),
    # Specialized / International
    ('Ghana Technology University College', 'Specialised technology university in Accra focused on ICT and engineering.'),
    ('African University College of Communications', 'Private university in Accra specialising in media, communications and journalism.'),
    ('BlueCrest University College', 'Private technology university in Accra focused on computing and digital skills.'),
    ('Regent University College of Science and Technology', 'Private university in Accra offering science, technology and business programmes.'),
    ('Knutsford University College', 'Private university college in Accra offering business and management programmes.'),
    ('Wisconsin International University College', 'Private university in Accra with a focus on business and information technology.'),
    ('Kings University College', 'Private university college in Accra offering business, law and social sciences.'),
    ('University of Professional Studies Accra', 'Public university in Accra specialising in business, management and professional studies.'),
]


def seed(apps, schema_editor):
    SchoolCommunity = apps.get_model('community', 'SchoolCommunity')
    for name, description in UNIVERSITIES:
        base_slug = slugify(name)
        slug = base_slug
        n = 1
        while SchoolCommunity.objects.filter(slug=slug).exists():
            # Only skip if it's the same name (already seeded)
            if SchoolCommunity.objects.filter(slug=slug, name=name).exists():
                break
            slug = f'{base_slug}-{n}'
            n += 1
        SchoolCommunity.objects.get_or_create(
            name=name,
            defaults={'slug': slug, 'description': description, 'verified': True, 'is_active': True},
        )


def unseed(apps, schema_editor):
    SchoolCommunity = apps.get_model('community', 'SchoolCommunity')
    SchoolCommunity.objects.filter(name__in=[u[0] for u in UNIVERSITIES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0007_add_topic_mature_restricted'),
    ]

    operations = [
        migrations.RunPython(seed, reverse_code=unseed),
    ]
