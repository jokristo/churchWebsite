from django import forms

from .models import Commentaire


class CommentaireForm(forms.ModelForm):
    class Meta:
        model = Commentaire
        fields = ['nom', 'email', 'contenu']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'w-full rounded-xl border border-gray-200 px-4 py-3 text-sm focus:ring-2 focus:ring-[#FF385C]/30 focus:border-[#FF385C] outline-none transition',
                'placeholder': 'Votre nom',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full rounded-xl border border-gray-200 px-4 py-3 text-sm focus:ring-2 focus:ring-[#FF385C]/30 focus:border-[#FF385C] outline-none transition',
                'placeholder': 'Votre e-mail (optionnel)',
            }),
            'contenu': forms.Textarea(attrs={
                'class': 'w-full rounded-xl border border-gray-200 px-4 py-3 text-sm focus:ring-2 focus:ring-[#FF385C]/30 focus:border-[#FF385C] outline-none transition resize-none',
                'placeholder': 'Partagez votre réflexion…',
                'rows': 4,
            }),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user and user.is_authenticated:
            self.fields['nom'].required = False
            self.fields['email'].required = False

    def clean_nom(self):
        nom = self.cleaned_data.get('nom', '').strip()
        if self.user and self.user.is_authenticated:
            return self.user.get_full_name() or self.user.username
        if not nom:
            raise forms.ValidationError("Veuillez indiquer votre nom.")
        return nom
