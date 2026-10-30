from rest_framework.pagination import CursorPagination


class PaginationCurseur(CursorPagination):
    """Pagination par curseur : stable pendant la synchronisation (pas de doublon ni de trou
    quand des contenus sont ajoutés entre deux pages), et liens next/previous absolus.

    - Ordre d'affichage : l'attribut `ordre` de la vue.
    - Avec ?updated_since= : date de modification croissante, pour que l'application
      reprenne la synchronisation là où elle s'est arrêtée.
    """

    page_size = 20
    page_size_query_param = "taille"
    max_page_size = 100
    ordering = "-id"

    def get_ordering(self, request, queryset, view):
        if request.query_params.get("updated_since") and getattr(view, "ordre_synchro", None):
            return view.ordre_synchro
        return getattr(view, "ordre", None) or self.ordering
