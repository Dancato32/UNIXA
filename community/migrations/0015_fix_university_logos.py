"""
Fix university logos — replace broken Wikimedia guessed URLs with
reliable ui-avatars.com generated logos + confirmed real URLs for major unis.
"""
from django.db import migrations

# ui-avatars.com generates a clean letter avatar with custom colors
# Format: https://ui-avatars.com/api/?name=UG&background=1a3a6b&color=fff&size=128&bold=true&rounded=true
def ua(initials, bg='1a3a6b', fg='ffffff'):
    return f'https://ui-avatars.com/api/?name={initials}&background={bg}&color={fg}&size=128&bold=true&rounded=true&font-size=0.4'

LOGOS = {
    # Traditional / Comprehensive — confirmed real Wikipedia image paths
    'University of Ghana':
        'https://upload.wikimedia.org/wikipedia/en/9/9e/University_of_Ghana_%28UG%29_logo.jpg',
    'Kwame Nkrumah University of Science and Technology':
        'https://upload.wikimedia.org/wikipedia/en/9/9e/Knust_seal.jpg',
    'University of Cape Coast':
        'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/University_of_Cape_Coast_crest.png/200px-University_of_Cape_Coast_crest.png',
    'Ashesi University':
        'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/Ashesi_University_logo.png/200px-Ashesi_University_logo.png',
    'Catholic University College of Ghana':
        'https://upload.wikimedia.org/wikipedia/en/thumb/c/c4/Catholic_university_college_of_Ghana_logo.png/200px-Catholic_university_college_of_Ghana_logo.png',

    # All others — reliable generated avatars with school colors
    'University of Education, Winneba':             ua('UEW', '006400'),
    'University for Development Studies':           ua('UDS', '8B0000'),
    'University of Mines and Technology':           ua('UMaT', '4a4a00'),
    'University of Health and Allied Sciences':     ua('UHAS', '006666'),
    'University of Energy and Natural Resources':   ua('UENR', '1a5276'),
    'University of Environment and Sustainable Development': ua('UESD', '145a32'),
    'Accra Technical University':                   ua('ATU', '1a237e'),
    'Kumasi Technical University':                  ua('KsTU', '4a235b'),
    'Cape Coast Technical University':              ua('CCTU', '1b4f72'),
    'Takoradi Technical University':                ua('TTU', '0b5345'),
    'Ho Technical University':                      ua('HTU', '6e2f0a'),
    'Koforidua Technical University':               ua('KTU', '1a5276'),
    'Tamale Technical University':                  ua('TaTU', '4d1a00'),
    'Bolgatanga Technical University':              ua('BTU', '1a3a1a'),
    'Central University':                           ua('CU', '7b241c'),
    'Valley View University':                       ua('VVU', '1a5276'),
    'Ghana Christian University College':           ua('GCUC', '1a3a6b'),
    'Methodist University Ghana':                   ua('MUG', '6e2f0a'),
    'Presbyterian University Ghana':                ua('PUG', '1a3a6b'),
    'Islamic University College Ghana':             ua('IUC', '145a32'),
    'Pentecost University':                         ua('PU', '7b241c'),
    'Garden City University College':               ua('GCUC', '0b5345'),
    'Lancaster University Ghana':                   ua('LU', 'b5121b'),
    'Academic City University College':             ua('ACity', '1a237e'),
    'Ghana Technology University College':          ua('GTUC', '1a3a6b'),
    'African University College of Communications': ua('AUCC', '4a235b'),
    'BlueCrest University College':                 ua('BC', '1565c0'),
    'Regent University College of Science and Technology': ua('RUCST', '4a235b'),
    'Knutsford University College':                 ua('KUC', '1a3a6b'),
    'Wisconsin International University College':   ua('WIUC', '7b241c'),
    'Kings University College':                     ua('KUC', '6e2f0a'),
    'University of Professional Studies Accra':     ua('UPSA', '1a3a6b'),
}


def seed(apps, schema_editor):
    SchoolCommunity = apps.get_model('community', 'SchoolCommunity')
    for name, url in LOGOS.items():
        SchoolCommunity.objects.filter(name=name).update(logo_url=url)
    # Any remaining schools without a logo get a generated one
    for school in SchoolCommunity.objects.filter(logo_url=''):
        initials = ''.join(w[0] for w in school.name.split() if w[0].isupper())[:3] or school.name[:2].upper()
        school.logo_url = ua(initials, '1a3a6b')
        school.save(update_fields=['logo_url'])


def unseed(apps, schema_editor):
    pass  # keep logos


class Migration(migrations.Migration):
    dependencies = [
        ('community', '0014_seed_school_logo_urls'),
    ]
    operations = [
        migrations.RunPython(seed, reverse_code=unseed),
    ]
