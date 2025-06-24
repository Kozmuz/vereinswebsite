from django.urls import path
from . import views
from .views import validate_qr
from main.views import qr_checkin_view

urlpatterns = [
    path("", views.home),
    path("about/", views.about),
    path("contact/", views.contact_view),
    path("anmeldung/ajax/", views.anmeldung_ajax_view, name="anmeldung_ajax"),
    path("anmeldung/", views.anmeldung_view, name="anmeldung"),
    path(
        "anmeldung-erfolgreich/", views.anmeldung_erfolg_view, name="anmeldung_erfolg"
    ),
    path("validate/<uuid:token>/", validate_qr, name="validate_qr"),
    path(
        "zahlung-bestaetigen/",
        views.zahlung_bestaetigen_view,
        name="zahlung_bestaetigen",
    ),
    path("checkin/<int:anmeldung_id>/", qr_checkin_view, name="qr_checkin"),
]
