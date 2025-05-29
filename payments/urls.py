from django.urls import path
from . import views

urlpatterns = [
    path('anmeldung/', views.anmeldung_view, name='anmeldung'),
    path('paypal/create-order/', views.create_order, name='create_order'),
    path('paypal/capture-order/', views.capture_order, name='capture_order'),
    path('anmeldung-erfolgreich/', views.anmeldung_erfolg_view, name='anmeldung_erfolg'),
]
