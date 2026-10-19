from django.contrib import admin, messages

from church.utils.audio import demander_compression


class CompressionAudioAdminMixin:
    """État de la compression visible dans l'admin, et action pour la relancer."""

    compression_readonly = ("audio_etat", "audio_detail", "audio_original", "audio_maj")
    actions = ["recompresser_audio"]

    def get_readonly_fields(self, request, obj=None):
        return tuple(super().get_readonly_fields(request, obj)) + self.compression_readonly

    def get_list_filter(self, request):
        return tuple(super().get_list_filter(request)) + ("audio_etat",)

    @admin.action(description="Compresser à nouveau l'audio")
    def recompresser_audio(self, request, queryset):
        champ = queryset.model.audio_field_name
        avec_audio = [obj for obj in queryset if getattr(obj, champ)]
        for obj in avec_audio:
            demander_compression(obj)
        self.message_user(
            request,
            f"{len(avec_audio)} audio(s) en cours de compression. Rechargez la page dans "
            "quelques minutes pour voir le résultat.",
            messages.SUCCESS,
        )
