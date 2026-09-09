from django.db import migrations


def populate(apps, schema_editor):
    Ministre = apps.get_model('OurData', 'Ministre')
    Orateur = apps.get_model('sermons', 'Orateur')

    data = {
        1: {'fonction': 'titulaire', 'ordre': 1, 'orateur_id': 1},
        3: {'fonction': 'associe', 'ordre': 2, 'orateur_id': 2},
        2: {'fonction': 'ministre', 'ordre': 3, 'orateur_id': None},
    }

    for ministre_id, values in data.items():
        Ministre.objects.filter(pk=ministre_id).update(
            fonction=values['fonction'],
            ordre=values['ordre'],
        )
        if values['orateur_id']:
            Orateur.objects.filter(pk=values['orateur_id']).update(ministre_id=ministre_id)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('OurData', '0008_ministre_fonction_orateur_link'),
        ('sermons', '0005_ministre_fonction_orateur_link'),
    ]

    operations = [
        migrations.RunPython(populate, noop),
    ]
