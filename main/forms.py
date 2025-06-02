from django import forms
from .models import Anmeldung


class Anmeldeformular(forms.ModelForm):
    class Meta:
        model = Anmeldung
        fields = ["vorname", "nachname", "email", "bemerkung", "termin", "fahrzeugtyp"]
        widgets = {
            "termin": forms.DateInput(attrs={"type": "date"}),
        }
