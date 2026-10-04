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


class SeoTests(TestCase):
    def test_robots_txt(self):
        response = self.client.get('/robots.txt')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sitemap: https://www.wmbranhamtabernacle.org/sitemap.xml')
        self.assertContains(response, 'Disallow: /admin/')

    def test_sitemap(self):
        from actualites.models import Article
        Article.objects.create(titre="Culte de Pâques", slug="culte-de-paques", resume="r", contenu="c", est_publie=True)
        Article.objects.create(titre="Brouillon", slug="brouillon", resume="r", contenu="c", est_publie=False)
        response = self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<loc>https://www.wmbranhamtabernacle.org/</loc>')
        self.assertContains(response, 'https://www.wmbranhamtabernacle.org/blog/culte-de-paques/')
        self.assertNotContains(response, 'brouillon')
        self.assertNotContains(response, 'connaissons-nous')

    def test_accueil_seo(self):
        response = self.client.get('/')
        self.assertContains(response, '<title>WMB Tabernacle – Église William Marrion Branham à Kinshasa</title>')
        self.assertContains(response, '<link rel="canonical" href="https://www.wmbranhamtabernacle.org/">')
        self.assertContains(response, '"@type": "Church"')
        self.assertContains(response, 'Mont-Ngafula, Kinshasa')
        self.assertContains(response, 'Nous rendre visite')
        self.assertContains(response, 'Dimanche</span> : à partir de 10h30')
        self.assertContains(response, 'Mercredi</span> : à partir de 17h')
        self.assertContains(response, '"dayOfWeek": "https://schema.org/Friday", "opens": "17:00"')

    def test_article_donnees_structurees(self):
        from actualites.models import Article
        Article.objects.create(titre="Culte de Pâques", slug="culte-de-paques", resume="Résumé", contenu="c", est_publie=True)
        response = self.client.get('/blog/culte-de-paques/')
        self.assertContains(response, '"@type": "BlogPosting"')
        self.assertContains(response, '<meta property="og:type" content="article">')

    def test_redirection_domaine_sans_www(self):
        response = self.client.get('/sermons/?theme=2', HTTP_HOST='wmbranhamtabernacle.org')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], 'https://www.wmbranhamtabernacle.org/sermons/?theme=2')

    def test_onrender_non_indexe(self):
        response = self.client.get('/', HTTP_HOST='wmbtab.onrender.com')
        self.assertEqual(response['X-Robots-Tag'], 'noindex, nofollow')

    def test_profil_fidele_non_indexe(self):
        from OurData.models import Croyant
        fidele = Croyant.objects.create(nom="Test", photo_profil="x.webp", adresse="a",
                                        etat_civil="e", ambitions="a", pourquoi_wmb="p")
        response = self.client.get(f'/connaissons-nous/{fidele.pk}/')
        self.assertContains(response, 'content="noindex, follow"')
