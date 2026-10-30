from django.urls import path
from rest_framework.routers import SimpleRouter

from api import views

app_name = "api"

routeur = SimpleRouter()
routeur.register("sermons", views.SermonViewSet, basename="sermon")
routeur.register("themes", views.ThemeViewSet, basename="theme")
routeur.register("orateurs", views.OrateurViewSet, basename="orateur")
routeur.register("ministres", views.MinistreViewSet, basename="ministre")
routeur.register("categories", views.CategorieViewSet, basename="categorie")
routeur.register("articles", views.ArticleViewSet, basename="article")
routeur.register("temoignages", views.TemoignageViewSet, basename="temoignage")

urlpatterns = [
    path("eglise/", views.EgliseView.as_view(), name="eglise"),
    path("suppressions/", views.SuppressionListView.as_view(), name="suppressions"),
    path("schema/", views.SchemaView.as_view(), name="schema"),
    path("docs/", views.DocumentationView.as_view(url_name="api:schema"), name="docs"),
] + routeur.urls
