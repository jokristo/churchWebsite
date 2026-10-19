"""Réglages HTTPS de production, activés par la variable SECURITE_PRODUCTION=1.

Activation explicite (et non automatique selon DEBUG) pour deux raisons :
- on peut les couper depuis Render en cas de problème, sans redéployer ;
- les tests et le développement local tournent en HTTP : une redirection forcée
  vers HTTPS les casserait.
"""

# Origines autorisées pour les formulaires (admin) : HTTPS seulement.
CSRF_TRUSTED_ORIGINS = [
    "https://www.wmbranhamtabernacle.org",
    "https://wmbranhamtabernacle.org",
    "https://*.onrender.com",
]

# Durée HSTS par défaut : courte, le temps de vérifier que tout le site fonctionne en
# HTTPS. Un navigateur qui a reçu l'en-tête refuse le HTTP pendant toute cette durée,
# même si on retire le réglage : on l'allonge ensuite par étapes (HSTS_SECONDES).
HSTS_PAR_DEFAUT = 3600


def _vrai(valeur):
    return (valeur or "").strip().lower() in ("1", "true", "yes", "oui")


def reglages_securite(env):
    """Réglages Django à ajouter à settings.py pour l'environnement donné."""
    reglages = {"CSRF_TRUSTED_ORIGINS": CSRF_TRUSTED_ORIGINS}
    if not _vrai(env.get("SECURITE_PRODUCTION")):
        return reglages
    reglages.update(
        # Render termine le HTTPS et transmet la requête en HTTP avec cet en-tête :
        # sans lui, Django croirait chaque requête non sécurisée.
        SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO", "https"),
        SECURE_SSL_REDIRECT=True,
        # Cookies de session et CSRF (admin) jamais envoyés en clair.
        SESSION_COOKIE_SECURE=True,
        CSRF_COOKIE_SECURE=True,
        SECURE_HSTS_SECONDS=int(env.get("HSTS_SECONDES") or HSTS_PAR_DEFAUT),
        SECURE_HSTS_INCLUDE_SUBDOMAINS=_vrai(env.get("HSTS_SOUS_DOMAINES")),
        # Jamais de preload : l'inscription dans les navigateurs est quasi irréversible.
        SECURE_HSTS_PRELOAD=False,
    )
    return reglages
