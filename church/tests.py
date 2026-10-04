"""Tests « smoke » : chaque page publique répond et chaque template se compile."""
from pathlib import Path

from django.conf import settings
from django.template.loader import get_template
from django.test import TestCase
from django.urls import reverse

PAGES_PUBLIQUES = [
    'home', 'sermons', 'ministres', 'temoignages', 'temoignagecontent', 'blog',
    'ViewTheme', 'categorieOfficiel', 'chantre', 'media_presse', 'biographie_pasteur',
    'connaissons_nous_liste', 'ecodim', 'contribution',
]


class PagesPubliquesTests(TestCase):
    def test_pages_publiques_repondent(self):
        for nom in PAGES_PUBLIQUES:
            with self.subTest(page=nom):
                response = self.client.get(reverse(nom))
                self.assertEqual(response.status_code, 200)

    def test_page_inexistante_renvoie_404(self):
        response = self.client.get('/cette-page-n-existe-pas/')
        self.assertEqual(response.status_code, 404)


class TemplatesTests(TestCase):
    def test_tous_les_templates_se_compilent(self):
        racine = Path(settings.BASE_DIR) / 'templates'
        for chemin in racine.rglob('*.html'):
            nom = chemin.relative_to(racine).as_posix()
            with self.subTest(template=nom):
                get_template(nom)


class AdminTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        admin = get_user_model().objects.create_superuser("admin", "a@a.org", "motdepasse")
        self.client.force_login(admin)

    def test_pages_admin_principales(self):
        for url in [
            'admin:actualites_commentaire_changelist',
            'admin:compte_utilisateur_changelist',
            'admin:compte_utilisateur_add',
        ]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(reverse(url)).status_code, 200)
