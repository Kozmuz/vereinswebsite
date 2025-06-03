from django.shortcuts import render
from django.conf import settings
from .forms import Anmeldeformular
from .models import Anmeldung
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import json
import os
from datetime import datetime

now_iso = datetime.utcnow().isoformat() + "Z"  # z.B. '2025-06-03T12:34:56.789Z'


def home(request):
    return render(request, "main/home.html")


def about(request):
    return render(request, "main/about.html")


def contact_view(request):
    return render(request, "main/contact.html")


def anmeldung_view(request):
    if request.method == "POST":
        form = Anmeldeformular(request.POST)
        if form.is_valid():
            anmeldung_obj = form.save()
            context = {
                "form": form,
                "anmeldung_id": anmeldung_obj.id,
                "PAYPAL_CLIENT_ID": settings.PAYPAL_CLIENT_ID,
            }
            return render(request, "main/anmeldung.html", context)
    else:
        form = Anmeldeformular()

    context = {"form": form, "PAYPAL_CLIENT_ID": settings.PAYPAL_CLIENT_ID}
    return render(request, "main/anmeldung.html", context)


def get_paypal_access_token():
    response = requests.post(
        f"{settings.PAYPAL_API_BASE_URL}/v1/oauth2/token",
        auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
        headers={"Accept": "application/json"},
        data={"grant_type": "client_credentials"},
    )
    response.raise_for_status()
    return response.json()["access_token"]


@csrf_exempt
def create_order(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            anmeldung_id = data.get("anmeldung_id")  # fehlt in deinem Beispiel
            amount = data.get("amount", "10.00")

            access_token = get_paypal_access_token()
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
            }

            order_data = {
                "intent": "CAPTURE",
                "purchase_units": [
                    {"amount": {"currency_code": "EUR", "value": amount}}
                ],
            }

            response = requests.post(
                f"{settings.PAYPAL_API_BASE_URL}/v2/checkout/orders",
                headers=headers,
                json=order_data,
            )
            response.raise_for_status()

            paypal_response = response.json()

            paypal_order_id = paypal_response.get("id")

            if anmeldung_id and paypal_order_id:
                try:
                    anmeldung = Anmeldung.objects.get(id=anmeldung_id)
                    anmeldung.paypal_order_id = paypal_order_id
                    anmeldung.save()
                except Anmeldung.DoesNotExist:
                    pass  # Optional: Loggen, falls Anmeldung nicht gefunden wird

            return JsonResponse(paypal_response)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid method"}, status=405)


@csrf_exempt
def capture_order(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            order_id = data.get("orderID")

            access_token = get_paypal_access_token()
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
            }

            response = requests.post(
                f"{settings.PAYPAL_API_BASE_URL}/v2/checkout/orders/{order_id}/capture",
                headers=headers,
            )
            response.raise_for_status()
            return JsonResponse(response.json())
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid method"}, status=405)


def anmeldung_erfolg_view(request):
    anmeldung_id = request.GET.get("anmeldung_id")
    return render(
        request,
        "main/anmeldung_erfolg.html",
        {"PAYPAL_CLIENT_ID": settings.PAYPAL_CLIENT_ID, "anmeldung_id": anmeldung_id},
    )


def anmeldung_ajax_view(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Ungültige JSON-Daten"}, status=400)

        form = Anmeldeformular(data)
        if form.is_valid():
            anmeldung = form.save()
            return JsonResponse({"anmeldung_id": anmeldung.id})
        else:
            return JsonResponse({"error": form.errors}, status=400)

    return JsonResponse({"error": "Nur POST erlaubt"}, status=405)


from supabase import create_client, Client


def zahlung_erfolgreich(request):
    anmeldung_id = request.GET.get("anmeldung_id")
    paypal_order_id = request.GET.get("paypal_order_id")  # Oder andersherum übergeben!

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase = create_client(url, key)

    if anmeldung_id and paypal_order_id:
        now_iso = datetime.utcnow().isoformat() + "Z"
        try:
            response = (
                supabase.table("anmeldungen")
                .update(
                    {
                        "bezahlmethode": "paypal",
                        "ist_bezahlt": True,
                        "paypal_order_id": paypal_order_id,
                        "zahlungsdatum": now_iso,
                    }
                )
                .eq("id", int(anmeldung_id))
                .execute()
            )
            print("Supabase-Update:", response)
        except Exception as e:
            print("Supabase-Fehler:", e)
    else:
        print("Anmeldung-ID oder PayPal-Order-ID fehlt.")

    return render(
        request, "main/zahlung_erfolgreich.html", {"anmeldung_id": anmeldung_id}
    )
