from django import forms

from .models import Commentaire


class CommentaireForm(forms.ModelForm):
    # Champ piège (honeypot) : invisible pour les humains, les robots le remplissent.
    site_web = forms.CharField(
        required=False,
        label="Ne pas remplir ce champ",
        widget=forms.TextInput(attrs={'autocomplete': 'off', 'tabindex': '-1'}),
    )

    class Meta:
        model = Commentaire
        fields = ['nom', 'email', 'contenu']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'w-full rounded-xl border border-slate-200 px-4 py-3 text-sm focus:ring-2 focus:ring-brand/30 focus:border-brand outline-none transition',
                'placeholder': 'Votre nom',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full rounded-xl border border-slate-200 px-4 py-3 text-sm focus:ring-2 focus:ring-brand/30 focus:border-brand outline-none transition',
                'placeholder': 'Votre e-mail (optionnel)',
            }),
            'contenu': forms.Textarea(attrs={
                'class': 'w-full rounded-xl border border-slate-200 px-4 py-3 text-sm focus:ring-2 focus:ring-brand/30 focus:border-brand outline-none transition resize-none',
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

    def est_spam(self):
        """True si le champ piège a été rempli (soumission automatisée)."""
        return bool(self.cleaned_data.get('site_web'))
