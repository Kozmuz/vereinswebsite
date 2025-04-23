from django import forms
from .models import Anmeldung

class Anmeldeformular(forms.ModelForm):
    class Meta:
        model = Anmeldung
        fields = ['vorname', 'nachname', 'email', 'bemerkung', 'termin', 'fahrzeugtyp', 'bezahlmethode']
    
    # Optional: Du kannst hier noch einige Anpassungen machen, z.B. für bestimmte Felder ein Widget hinzufügen
    termin = forms.DateField(widget=forms.SelectDateWidget(years=range(2023, 2030)))  # Kalender für Termin
    fahrzeugtyp = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Fahrzeugtyp'}))
    bezahlmethode = forms.ChoiceField(
        choices=[('Kreditkarte', 'Kreditkarte'), ('PayPal', 'PayPal'), ('Überweisung', 'Überweisung')],
        widget=forms.Select(attrs={'placeholder': 'Wählen Sie eine Bezahlmethode'})
    )
