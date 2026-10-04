from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from .models import Article, Categorie, Commentaire


class ModerationCommentairesTests(TestCase):
    def setUp(self):
        cache.clear()
        categorie = Categorie.objects.create(nom="Annonces", slug="annonces")
        self.article = Article.objects.create(
            titre="Culte de dimanche",
            slug="culte-de-dimanche",
            categorie=categorie,
            resume="Résumé",
            contenu="Contenu",
            est_publie=True,
        )
        self.url = reverse('blog_detail', args=[self.article.slug])

    def poster(self, **extra):
        data = {'commentaire': '1', 'nom': 'Visiteur', 'email': '', 'contenu': 'Amen !'}
        data.update(extra)
        return self.client.post(self.url, data, follow=True)

    def test_commentaire_visiteur_en_attente(self):
        self.poster()
        commentaire = Commentaire.objects.get()
        self.assertFalse(commentaire.est_approuve)

    def test_commentaire_en_attente_non_affiche(self):
        response = self.poster(contenu="Texte en attente de validation")
        self.assertNotContains(response, "Texte en attente de validation")
        self.assertContains(response, "après validation")

    def test_commentaire_approuve_affiche(self):
        Commentaire.objects.create(
            article=self.article, nom="Frère Paul", contenu="Gloire à Dieu", est_approuve=True
        )
        response = self.client.get(self.url)
        self.assertContains(response, "Gloire à Dieu")

    def test_honeypot_bloque_les_robots(self):
        self.poster(site_web="http://spam.example")
        self.assertEqual(Commentaire.objects.count(), 0)

    def test_limite_un_commentaire_par_minute(self):
        self.poster(contenu="Premier")
        response = self.poster(contenu="Deuxième")
        self.assertEqual(Commentaire.objects.count(), 1)
        self.assertContains(response, "patienter")

    def test_commentaire_staff_publie_directement(self):
        staff = get_user_model().objects.create_user("admin", password="x", is_staff=True)
        self.client.force_login(staff)
        self.poster(nom='')
        self.assertTrue(Commentaire.objects.get().est_approuve)
