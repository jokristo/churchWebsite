from django.forms import ModelForm

from OurData.models import Temoignages


class TemoignageForm(ModelForm):
    class Meta:
        model = Temoignages
        fields = [
            "NomDuCroyant",
            "Description",
            "photo",
            "Audio",
        ]
