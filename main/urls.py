from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),      # ← Startseite
    path('about/', views.about, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('anmeldung/', views.anmeldung_view, name='anmeldung'),
    path('anmeldung/erfolg/', views.anmeldung_erfolg_view, name='anmeldung_erfolg'),
]