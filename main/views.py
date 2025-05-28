from django.shortcuts import render, redirect
from django.conf import settings
from .forms import Anmeldeformular
from .models import Anmeldung

def home(request):
    return render(request, 'main/home.html')

def about(request):
    return render(request, 'main/about.html')

def contact_view(request):
    return render(request, 'main/contact.html')

def anmeldung_view(request):
    if request.method == 'POST':
        form = Anmeldeformular(request.POST)
        if form.is_valid():
            anmeldung_obj = form.save()

            context = {
                'form': form,
                'anmeldung_id': anmeldung_obj.id,
                'PAYPAL_CLIENT_ID': settings.PAYPAL_CLIENT_ID
            }
            return render(request, 'main/anmeldung.html', context)
    else:
        form = Anmeldeformular()

    context = {
        'form': form,
        'PAYPAL_CLIENT_ID': settings.PAYPAL_CLIENT_ID
    }
    return render(request, 'main/anmeldung.html', context)

def anmeldung_erfolg_view(request):
    return render(request, 'main/anmeldung_erfolg.html')
