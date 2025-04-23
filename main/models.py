from django.db import models

class Anmeldung(models.Model):
    # Vorname, Nachname, Email, Bemerkung, Erstellungsdatum
    vorname = models.CharField(max_length=100)
    nachname = models.CharField(max_length=100)
    email = models.EmailField()
    bemerkung = models.TextField(blank=True)
    erstellt_am = models.DateTimeField(auto_now_add=True)

    # Neues Feld für den Termin (Datum)
    termin = models.DateField()

    # Neues Feld für Fahrzeugtyp
    fahrzeugtyp = models.CharField(max_length=100)

    # Neues Feld für die Bezahlmethode
    bezahlmethode = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.vorname} {self.nachname}"
