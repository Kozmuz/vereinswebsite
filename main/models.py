from django.db import models

class Anmeldung(models.Model):
    vorname = models.CharField(max_length=100)
    nachname = models.CharField(max_length=100)
    email = models.EmailField()
    bemerkung = models.TextField(blank=True)
    erstellt_am = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.vorname} {self.nachname}"
