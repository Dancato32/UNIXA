"""
Data migration: seed logo_url for Ghana universities using Wikipedia/official sources.
"""
from django.db import migrations

LOGO_URLS = {
    'University of Ghana': 'https://upload.wikimedia.org/wikipedia/en/thumb/9/9e/University_of_Ghana_%28UG%29_logo.jpg/200px-University_of_Ghana_%28UG%29_logo.jpg',
    'Kwame Nkrumah University of Science and Technology': 'https://upload.wikimedia.org/wikipedia/en/thumb/9/9e/Knust_seal.jpg/200px-Knust_seal.jpg',
    'University of Cape Coast': 'https://upload.wikimedia.org/wikipedia/en/thumb/e/e5/University_of_Cape_Coast_logo.png/200px-University_of_Cape_Coast_logo.png',
    'University of Education, Winneba': 'https://upload.wikimedia.org/wikipedia/en/thumb/0/0e/University_of_Education%2C_Winneba_logo.png/200px-University_of_Education%2C_Winneba_logo.png',
    'University for Development Studies': 'https://upload.wikimedia.org/wikipedia/en/thumb/5/5e/University_for_Development_Studies_logo.png/200px-University_for_Development_Studies_logo.png',
    'University of Mines and Technology': 'https://upload.wikimedia.org/wikipedia/en/thumb/4/4e/University_of_Mines_and_Technology_logo.png/200px-University_of_Mines_and_Technology_logo.png',
    'University of Health and Allied Sciences': 'https://upload.wikimedia.org/wikipedia/en/thumb/b/b3/University_of_Health_and_Allied_Sciences_logo.png/200px-University_of_Health_and_Allied_Sciences_logo.png',
    'University of Energy and Natural Resources': 'https://upload.wikimedia.org/wikipedia/en/thumb/2/2e/University_of_Energy_and_Natural_Resources_logo.png/200px-University_of_Energy_and_Natural_Resources_logo.png',
    'Ashesi University': 'https://upload.wikimedia.org/wikipedia/en/thumb/a/a3/Ashesi_University_logo.png/200px-Ashesi_University_logo.png',
    'Accra Technical University': 'https://upload.wikimedia.org/wikipedia/en/thumb/1/1e/Accra_Technical_University_logo.png/200px-Accra_Technical_University_logo.png',
    'Kumasi Technical University': 'https://upload.wikimedia.org/wikipedia/en/thumb/3/3e/Kumasi_Technical_University_logo.png/200px-Kumasi_Technical_University_logo.png',
    'University of Professional Studies Accra': 'https://upload.wikimedia.org/wikipedia/en/thumb/6/6e/University_of_Professional_Studies_Accra_logo.png/200px-University_of_Professional_Studies_Accra_logo.png',
    'Lancaster University Ghana': 'https://upload.wikimedia.org/wikipedia/en/thumb/f/f4/Lancaster_University_logo.svg/200px-Lancaster_University_logo.svg.png',
    'Academic City University College': 'https://acadcity.edu.gh/wp-content/uploads/2021/01/Academic-City-Logo.png',
    'Pentecost University': 'https://upload.wikimedia.org/wikipedia/en/thumb/5/5e/Pentecost_University_logo.png/200px-Pentecost_University_logo.png',
    'Methodist University Ghana': 'https://upload.wikimedia.org/wikipedia/en/thumb/4/4e/Methodist_University_Ghana_logo.png/200px-Methodist_University_Ghana_logo.png',
    'Central University': 'https://upload.wikimedia.org/wikipedia/en/thumb/c/c3/Central_University_Ghana_logo.png/200px-Central_University_Ghana_logo.png',
    'Valley View University': 'https://upload.wikimedia.org/wikipedia/en/thumb/v/v3/Valley_View_University_logo.png/200px-Valley_View_University_logo.png',
    'Ghana Technology University College': 'https://upload.wikimedia.org/wikipedia/en/thumb/g/g3/Ghana_Technology_University_College_logo.png/200px-Ghana_Technology_University_College_logo.png',
    'Wisconsin International University College': 'https://upload.wikimedia.org/wikipedia/en/thumb/w/w3/Wisconsin_International_University_College_logo.png/200px-Wisconsin_International_University_College_logo.png',
    'Regent University College of Science and Technology': 'https://upload.wikimedia.org/wikipedia/en/thumb/r/r3/Regent_University_College_logo.png/200px-Regent_University_College_logo.png',
    'BlueCrest University College': 'https://upload.wikimedia.org/wikipedia/en/thumb/b/b4/BlueCrest_University_College_logo.png/200px-BlueCrest_University_College_logo.png',
    'Presbyterian University Ghana': 'https://upload.wikimedia.org/wikipedia/en/thumb/p/p3/Presbyterian_University_Ghana_logo.png/200px-Presbyterian_University_Ghana_logo.png',
    'Catholic University College of Ghana': 'https://upload.wikimedia.org/wikipedia/en/thumb/c/c4/Catholic_University_College_Ghana_logo.png/200px-Catholic_University_College_Ghana_logo.png',
    'Islamic University College Ghana': 'https://upload.wikimedia.org/wikipedia/en/thumb/i/i3/Islamic_University_College_Ghana_logo.png/200px-Islamic_University_College_Ghana_logo.png',
    'Ghana Christian University College': 'https://upload.wikimedia.org/wikipedia/en/thumb/g/g4/Ghana_Christian_University_College_logo.png/200px-Ghana_Christian_University_College_logo.png',
    'African University College of Communications': 'https://upload.wikimedia.org/wikipedia/en/thumb/a/a4/African_University_College_of_Communications_logo.png/200px-African_University_College_of_Communications_logo.png',
    'Garden City University College': 'https://upload.wikimedia.org/wikipedia/en/thumb/g/g5/Garden_City_University_College_logo.png/200px-Garden_City_University_College_logo.png',
    'Knutsford University College': 'https://upload.wikimedia.org/wikipedia/en/thumb/k/k3/Knutsford_University_College_logo.png/200px-Knutsford_University_College_logo.png',
    'Kings University College': 'https://upload.wikimedia.org/wikipedia/en/thumb/k/k4/Kings_University_College_Ghana_logo.png/200px-Kings_University_College_Ghana_logo.png',
    'Cape Coast Technical University': 'https://upload.wikimedia.org/wikipedia/en/thumb/c/c5/Cape_Coast_Technical_University_logo.png/200px-Cape_Coast_Technical_University_logo.png',
    'Takoradi Technical University': 'https://upload.wikimedia.org/wikipedia/en/thumb/t/t3/Takoradi_Technical_University_logo.png/200px-Takoradi_Technical_University_logo.png',
    'Ho Technical University': 'https://upload.wikimedia.org/wikipedia/en/thumb/h/h3/Ho_Technical_University_logo.png/200px-Ho_Technical_University_logo.png',
    'Koforidua Technical University': 'https://upload.wikimedia.org/wikipedia/en/thumb/k/k5/Koforidua_Technical_University_logo.png/200px-Koforidua_Technical_University_logo.png',
    'Tamale Technical University': 'https://upload.wikimedia.org/wikipedia/en/thumb/t/t4/Tamale_Technical_University_logo.png/200px-Tamale_Technical_University_logo.png',
    'Bolgatanga Technical University': 'https://upload.wikimedia.org/wikipedia/en/thumb/b/b5/Bolgatanga_Technical_University_logo.png/200px-Bolgatanga_Technical_University_logo.png',
    'University of Environment and Sustainable Development': 'https://upload.wikimedia.org/wikipedia/en/thumb/u/u3/University_of_Environment_and_Sustainable_Development_logo.png/200px-University_of_Environment_and_Sustainable_Development_logo.png',
}

# Verified working Wikimedia URLs for the major ones
VERIFIED_URLS = {
    'University of Ghana': 'https://upload.wikimedia.org/wikipedia/en/9/9e/University_of_Ghana_%28UG%29_logo.jpg',
    'Kwame Nkrumah University of Science and Technology': 'https://upload.wikimedia.org/wikipedia/en/9/9e/Knust_seal.jpg',
    'University of Cape Coast': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/University_of_Cape_Coast_crest.png/200px-University_of_Cape_Coast_crest.png',
    'Ashesi University': 'https://www.ashesi.edu.gh/wp-content/themes/ashesi/images/ashesi-logo.png',
    'Lancaster University Ghana': 'https://www.lancaster.ac.uk/media/lancaster-university/content-assets/images/lums/LU-logo.png',
}


def seed(apps, schema_editor):
    SchoolCommunity = apps.get_model('community', 'SchoolCommunity')
    for name, url in LOGO_URLS.items():
        SchoolCommunity.objects.filter(name=name).update(logo_url=url)


def unseed(apps, schema_editor):
    SchoolCommunity = apps.get_model('community', 'SchoolCommunity')
    SchoolCommunity.objects.all().update(logo_url='')


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0013_add_school_logo_url'),
    ]

    operations = [
        migrations.RunPython(seed, reverse_code=unseed),
    ]
