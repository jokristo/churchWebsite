from django.db import migrations


def _normalize(value):
    return ''.join(ch for ch in (value or '').lower() if ch.isalnum())


def _first_matching(queryset, field, *needles):
    for obj in queryset:
        haystack = _normalize(getattr(obj, field))
        if all(needle in haystack for needle in needles):
            return obj
    return None


def populate(apps, schema_editor):
    Ministre = apps.get_model('OurData', 'Ministre')
    Orateur = apps.get_model('sermons', 'Orateur')

    ministres = list(Ministre.objects.all())
    orateurs = list(Orateur.objects.all())
    if not ministres:
        return

    links = [
        (('munanga',), 'titulaire', 1, ('munanga',)),
        (('luzolo',), 'associe', 2, ('luzolo',)),
        (('meschac',), 'ministre', 3, None),
        (('kristo',), 'ministre', 3, None),
    ]
    seen = set()

    for ministre_needles, fonction, ordre, orateur_needles in links:
        ministre = _first_matching(ministres, 'Nom', *ministre_needles)
        if ministre is None or ministre.pk in seen:
            continue
        seen.add(ministre.pk)
        Ministre.objects.filter(pk=ministre.pk).update(fonction=fonction, ordre=ordre)
        if not orateur_needles:
            continue
        orateur = _first_matching(orateurs, 'Noms', *orateur_needles)
        if orateur is not None:
            Orateur.objects.filter(pk=orateur.pk).update(ministre_id=ministre.pk)


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
