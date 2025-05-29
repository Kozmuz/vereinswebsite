from django.shortcuts import render, redirect
from django.conf import settings
from .forms import Anmeldeformular
from .models import Anmeldung
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Anmeldung
import json

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
            anmeldung = form.save()  # speichert die Anmeldung in der DB
            # Danach Formular nochmal anzeigen, mit versteckter Anmeldung-ID für PayPal
            return render(request, 'main/anmeldung.html', {
                'form': form,
                'anmeldung': anmeldung  # WICHTIG: wird im Template benötigt
            })
    else:
        form = Anmeldeformular()
        anmeldung = None

    return render(request, 'main/anmeldung.html', {
        'form': form,
        'anmeldung': anmeldung
    })

def create_order(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            anmeldung_id = data.get("anmeldung_id")
            amount = data.get("amount")  # falls du später validieren willst

            # Simuliere eine echte Order-ID von PayPal
            fake_order_id = "ORDER-" + str(anmeldung_id)

            return JsonResponse({"id": fake_order_id})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid method"}, status=405)

def capture_order(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            order_id = data.get("orderID")

            # Simuliere PayPal Capture – später hier echte API-Integration
            return JsonResponse({"status": "COMPLETED", "id": order_id})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid method"}, status=405)

def anmeldung_erfolg_view(request):
    return render(request, 'main/anmeldung_erfolg.html')