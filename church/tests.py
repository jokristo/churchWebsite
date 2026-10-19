"""Tests « smoke » : chaque page publique répond et chaque template se compile."""
import re
from pathlib import Path

from django.conf import settings
from django.core import checks
from django.core.management.utils import get_random_secret_key
from django.template.loader import get_template
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from church.securite import CSRF_TRUSTED_ORIGINS, reglages_securite

PRODUCTION = reglages_securite({"SECURITE_PRODUCTION": "1"})

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


class ChargementTests(TestCase):
    """Poids et retour visuel pendant le chargement (public mobile, données chères)."""

    def balises(self, nom):
        racine = Path(settings.BASE_DIR) / 'templates'
        for chemin in racine.rglob('*.html'):
            for balise in re.findall(rf'<{nom}\b[^>]*>', chemin.read_text(encoding='utf-8'), re.S):
                yield chemin.relative_to(racine).as_posix(), balise

    def test_chaque_image_declare_son_chargement(self):
        # loading="lazy" hors de l'écran initial, loading="eager" pour le haut de page
        for template, balise in self.balises('img'):
            with self.subTest(template=template, balise=balise[:80]):
                self.assertRegex(balise, r'loading="(lazy|eager)"')

    def test_audio_non_precharge(self):
        # Un sermon pèse jusqu'à 40 Mo : rien n'est téléchargé avant que l'on appuie sur lecture
        for template, balise in self.balises('audio'):
            with self.subTest(template=template):
                self.assertIn('preload="none"', balise)

    def test_barre_de_progression(self):
        response = self.client.get('/')
        self.assertContains(response, '<div id="wmb-progress" class="wmb-progress" aria-hidden="true"></div>')

    def test_spinner_sur_les_boutons_like(self):
        from actualites.models import Article
        Article.objects.create(titre="Culte de Pâques", slug="culte-de-paques", resume="r", contenu="c", est_publie=True)
        for url in ['/blog/', '/blog/culte-de-paques/']:
            with self.subTest(url=url):
                self.assertContains(self.client.get(url), 'like-spinner')


class PagesErreurTests(TestCase):
    """Avec DEBUG=False (production), les visiteurs voient nos pages, pas celles de Django."""

    def test_404_personnalisee(self):
        response = self.client.get('/cette-page-n-existe-pas/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'errors/404.html')

    def test_500_personnalisee(self):
        from church import urls
        response = urls.handler500(RequestFactory().get('/'))
        self.assertEqual(response.status_code, 500)
        self.assertContains(response, '<title>', status_code=500)


class SecuriteProductionTests(TestCase):
    def test_inactif_par_defaut(self):
        # Développement et tests en HTTP : aucune redirection ni cookie Secure
        self.assertEqual(reglages_securite({}), {"CSRF_TRUSTED_ORIGINS": CSRF_TRUSTED_ORIGINS})
        self.assertEqual(self.client.get('/').status_code, 200)

    def test_reglages_actifs(self):
        self.assertEqual(PRODUCTION["SECURE_PROXY_SSL_HEADER"], ("HTTP_X_FORWARDED_PROTO", "https"))
        self.assertTrue(PRODUCTION["SECURE_SSL_REDIRECT"])
        self.assertTrue(PRODUCTION["SESSION_COOKIE_SECURE"])
        self.assertTrue(PRODUCTION["CSRF_COOKIE_SECURE"])
        self.assertEqual(PRODUCTION["SECURE_HSTS_SECONDS"], 3600)
        self.assertFalse(PRODUCTION["SECURE_HSTS_INCLUDE_SUBDOMAINS"])
        self.assertFalse(PRODUCTION["SECURE_HSTS_PRELOAD"])

    def test_hsts_reglable_par_etapes(self):
        reglages = reglages_securite({"SECURITE_PRODUCTION": "1", "HSTS_SECONDES": "2592000", "HSTS_SOUS_DOMAINES": "1"})
        self.assertEqual(reglages["SECURE_HSTS_SECONDS"], 2592000)
        self.assertTrue(reglages["SECURE_HSTS_INCLUDE_SUBDOMAINS"])
        self.assertFalse(reglages["SECURE_HSTS_PRELOAD"])

    def test_check_deploy(self):
        # Seuls restent les deux choix volontaires du démarrage progressif :
        # pas encore de HSTS sur les sous-domaines, et jamais de preload.
        with override_settings(DEBUG=False, SECRET_KEY=get_random_secret_key(), **PRODUCTION):
            ids = {msg.id for msg in checks.run_checks(include_deployment_checks=True)}
        self.assertEqual(ids - {"security.W005", "security.W021"}, set())

    @override_settings(**PRODUCTION)
    def test_http_redirige_vers_https(self):
        response = self.client.get('/sermons/?theme=2')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], 'https://testserver/sermons/?theme=2')

    @override_settings(**PRODUCTION)
    def test_https_derriere_render(self):
        # Render transmet la requête avec X-Forwarded-Proto: https
        response = self.client.get('/admin/login/', HTTP_X_FORWARDED_PROTO='https')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Strict-Transport-Security'], 'max-age=3600')
        self.assertTrue(response.cookies['csrftoken']['secure'])

    @override_settings(**PRODUCTION)
    def test_connexion_admin_en_https(self):
        # Le contrôle CSRF compare l'origine du formulaire à https://<domaine>
        from django.contrib.auth import get_user_model
        get_user_model().objects.create_superuser("admin", "a@a.org", "motdepasse")
        client = self.client_class(enforce_csrf_checks=True)
        entetes = {'HTTP_X_FORWARDED_PROTO': 'https', 'HTTP_HOST': 'www.wmbranhamtabernacle.org'}
        client.get('/admin/login/', **entetes)
        response = client.post('/admin/login/', {
            'username': 'admin', 'password': 'motdepasse', 'next': '/admin/',
            'csrfmiddlewaretoken': client.cookies['csrftoken'].value,
        }, HTTP_ORIGIN='https://www.wmbranhamtabernacle.org', **entetes)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/admin/')


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
        self.assertContains(response, '>Dimanche</p>')
        self.assertContains(response, '>10h30</p>')
        self.assertContains(response, '>Mercredi</p>')
        self.assertContains(response, '>17h</p>')
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
