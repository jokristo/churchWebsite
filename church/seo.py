"""
Informations officielles de l'église, utilisées pour le référencement (SEO).

Ces données alimentent :
- les balises <title>, canonical et Open Graph (via le context processor ``seo``),
- les données structurées schema.org (JSON-LD) lues par Google et son IA,
- le bloc « Nous rendre visite » de la page d'accueil.

Elles doivent être IDENTIQUES partout sur le web (site, fiche Google, Facebook,
YouTube…) : nom, adresse et téléphone écrits exactement de la même façon.
"""
import json
from urllib.parse import quote_plus

from django.conf import settings
from django.templatetags.static import static
from django.utils.safestring import mark_safe

EGLISE = {
    "nom": "William Marrion Branham Tabernacle de Mont-Ngafula",
    "noms_alternatifs": [
        "WMB Tabernacle",
        "WMB Tab",
        "Église William Branham de Mont-Ngafula",
    ],
    "description": (
        "Église chrétienne de Kinshasa (Mont-Ngafula) attachée au Message du "
        "prophète William Marrion Branham : cultes, prédications, école du "
        "dimanche et vie communautaire."
    ),
    "telephone": "+243999956607",
    "whatsapp": "https://wa.me/243897779439",
    "adresse": {
        "rue": "41, avenue Les Adorateurs",
        "commune": "Mont-Ngafula",
        "ville": "Kinshasa",
        "pays": "CD",
        "repere": "Triangle Campus, arrêt Révolution",
    },
    # Coordonnées GPS de l'entrée de l'église (ex. 4.4300, 15.2700).
    # Clic droit sur le lieu dans Google Maps pour les copier. Laisser None si inconnues.
    "latitude": None,
    "longitude": None,
    # Horaires des cultes : (jour en anglais, heure de début, heure de fin ou None).
    # Les jours sont en anglais car c'est le format attendu par Google (schema.org).
    "horaires": [
        ("Wednesday", "17:00", None),
        ("Friday", "17:00", None),
        ("Sunday", "10:30", None),
    ],
    "reseaux": [
        "https://web.facebook.com/wmbtabdemontngafula/",
        "https://www.youtube.com/@pasteurrbob",
    ],
}

JOURS_FR = {
    "Monday": "Lundi", "Tuesday": "Mardi", "Wednesday": "Mercredi", "Thursday": "Jeudi",
    "Friday": "Vendredi", "Saturday": "Samedi", "Sunday": "Dimanche",
}


def site_url():
    return settings.SITE_URL.rstrip("/")


def url_absolue(chemin):
    if not chemin:
        return ""
    if chemin.startswith("http://") or chemin.startswith("https://"):
        return chemin
    return site_url() + chemin


def en_jsonld(data):
    """Sérialise en JSON sûr pour une balise <script> (échappe les '<')."""
    texte = json.dumps(data, ensure_ascii=False, indent=None)
    return mark_safe(texte.replace("<", "\\u003c"))


def eglise_schema():
    a = EGLISE["adresse"]
    data = {
        "@context": "https://schema.org",
        "@type": "Church",
        "@id": site_url() + "/#eglise",
        "name": EGLISE["nom"],
        "alternateName": EGLISE["noms_alternatifs"],
        "description": EGLISE["description"],
        "url": site_url() + "/",
        "logo": url_absolue(static("logo24.png")),
        "image": url_absolue(static("church3m.jpg")),
        "telephone": EGLISE["telephone"],
        "address": {
            "@type": "PostalAddress",
            "streetAddress": a["rue"],
            "addressLocality": a["commune"],
            "addressRegion": a["ville"],
            "addressCountry": a["pays"],
        },
        "areaServed": "Kinshasa",
        "sameAs": EGLISE["reseaux"],
    }
    if EGLISE["latitude"] is not None and EGLISE["longitude"] is not None:
        data["geo"] = {
            "@type": "GeoCoordinates",
            "latitude": EGLISE["latitude"],
            "longitude": EGLISE["longitude"],
        }
    if EGLISE["horaires"]:
        specs = []
        for jour, debut, fin in EGLISE["horaires"]:
            spec = {
                "@type": "OpeningHoursSpecification",
                "dayOfWeek": f"https://schema.org/{jour}",
                "opens": debut,
            }
            if fin:
                spec["closes"] = fin
            specs.append(spec)
        data["openingHoursSpecification"] = specs
    site = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "@id": site_url() + "/#site",
        "name": "WMB Tabernacle de Mont-Ngafula",
        "url": site_url() + "/",
        "inLanguage": "fr",
        "publisher": {"@id": site_url() + "/#eglise"},
    }
    return [data, site]


def _heure_fr(heure):
    """'17:00' -> '17h', '10:30' -> '10h30'."""
    h, m = heure.split(":")
    return f"{int(h)}h" if m == "00" else f"{int(h)}h{m}"


def horaires_lisibles():
    lignes = []
    for jour, debut, fin in EGLISE["horaires"]:
        if fin:
            texte = f"de {_heure_fr(debut)} à {_heure_fr(fin)}"
        else:
            texte = f"à partir de {_heure_fr(debut)}"
        lignes.append({
            "jour": JOURS_FR.get(jour, jour),
            "texte": texte,
            "heure": _heure_fr(debut),
        })
    return lignes


def maps_search_url():
    a = EGLISE["adresse"]
    query = f"{a['rue']}, {a['commune']}, {a['ville']}"
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(query)}"


def seo(request):
    """Context processor : variables SEO disponibles dans tous les templates."""
    return {
        "site_url": site_url(),
        "canonical_url": site_url() + request.path,
        "eglise": EGLISE,
        "eglise_horaires": horaires_lisibles(),
        "eglise_maps_url": maps_search_url(),
        "eglise_jsonld": en_jsonld(eglise_schema()),
        "og_image_defaut": url_absolue(static("church3m.jpg")),
    }


def article_schema(article):
    """Données structurées d'un article de blog (BlogPosting)."""
    from django.urls import reverse

    data = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": article.titre[:110],
        "description": (article.resume or "")[:300],
        "url": site_url() + reverse("blog_detail", args=[article.slug]),
        "datePublished": article.date_publication.isoformat(),
        "dateModified": article.date_modification.isoformat(),
        "inLanguage": "fr",
        "publisher": {"@id": site_url() + "/#eglise"},
        "isPartOf": {"@id": site_url() + "/#site"},
    }
    if article.image_couverture:
        data["image"] = url_absolue(article.image_couverture.url)
    if article.auteur:
        data["author"] = {
            "@type": "Person",
            "name": article.auteur.get_full_name() or article.auteur.username,
        }
    else:
        data["author"] = {"@id": site_url() + "/#eglise"}
    return en_jsonld(data)
