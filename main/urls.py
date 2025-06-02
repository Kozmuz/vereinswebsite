from django.urls import path
from . import views

urlpatterns = [
    path("", views.home),
    path("about/", views.about),
    path("contact/", views.contact_view),
    path("anmeldung/ajax/", views.anmeldung_ajax_view, name="anmeldung_ajax"),
    path("anmeldung/", views.anmeldung_view, name="anmeldung"),
    path(
        "anmeldung-erfolgreich/", views.anmeldung_erfolg_view, name="anmeldung_erfolg"
    ),
]
