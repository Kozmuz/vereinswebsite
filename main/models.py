from django.db import models

class Anmeldung(models.Model):
    vorname = models.CharField(max_length=100)
    nachname = models.CharField(max_length=100)
    email = models.EmailField()
    bemerkung = models.TextField(blank=True, null=True)
    termin = models.DateField()
    fahrzeugtyp = models.CharField(max_length=50, choices=[('Auto', 'Auto'), ('Motorrad', 'Motorrad'), ('Fahrrad', 'Fahrrad')])
    bezahlmethode = models.CharField(max_length=50) # Dein Formular hat dies
    
    # NEU: Felder für PayPal-Integration
    paypal_order_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    ist_bezahlt = models.BooleanField(default=False)
    zahlungsdatum = models.DateTimeField(null=True, blank=True) # Optional
    
    def __str__(self):
        return f"{self.vorname} {self.nachname} - {self.termin}"