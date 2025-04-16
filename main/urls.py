from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),      # ← Startseite
    path('about/', views.about, name='about'),
    path('contact/', views.contact_view, name='contact'),
]
