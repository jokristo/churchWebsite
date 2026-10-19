from urllib.parse import urlparse

from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from actualites.models import Article
from OurData.models import CategorieOfficiel, Ministre
from sermons.models import Theme


class BaseSitemap(Sitemap):
    """Force le domaine officiel (www.wmbranhamtabernacle.org) et https."""
    protocol = "https"

    def get_domain(self, site=None):
        return urlparse(settings.SITE_URL).netloc


class PagesSitemap(BaseSitemap):
    changefreq = "weekly"

    PRIORITES = {"home": 1.0, "sermons": 0.9, "blog": 0.9, "ministres": 0.8}

    def items(self):
        return [
            "home", "sermons", "blog", "ministres", "ViewTheme", "biographie_pasteur",
            "temoignagecontent", "temoignages", "chantre", "categorieOfficiel",
            "media_presse", "ecodim", "contribution",
        ]

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return self.PRIORITES.get(item, 0.6)


class ArticlesSitemap(BaseSitemap):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return Article.objects.filter(est_publie=True)

    def location(self, article):
        return reverse("blog_detail", args=[article.slug])

    def lastmod(self, article):
        return article.date_modification


class ThemesSitemap(BaseSitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return Theme.objects.order_by("id")

    def location(self, theme):
        return reverse("SermonByTheme", args=[theme.id])


class MinistresSitemap(BaseSitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return Ministre.objects.order_by("id")

    def location(self, ministre):
        return reverse("ThemeByMinister", args=[ministre.id])


class OfficielsSitemap(BaseSitemap):
    changefreq = "monthly"
    priority = 0.4

    def items(self):
        return CategorieOfficiel.objects.order_by("id")

    def location(self, categorie):
        return reverse("officiels", args=[categorie.id])


SITEMAPS = {
    "pages": PagesSitemap,
    "articles": ArticlesSitemap,
    "themes": ThemesSitemap,
    "ministres": MinistresSitemap,
    "officiels": OfficielsSitemap,
}
