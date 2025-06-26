import json
import uuid
import logging
import requests
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import render
from django.utils import timezone

from main.utils.qr_code_utils import generate_qr_code, upload_qr_to_supabase
from main.models import Anmeldung, Participant

logger = logging.getLogger(__name__)


def anmeldung_erfolg_view(request):
    return render(request, "anmeldung_erfolg.html")


def checkout(request):
    return HttpResponse("Hier kommt später das Stripe-Bezahlformular.")


def get_paypal_access_token():
    auth_url = f"{settings.PAYPAL_API_BASE_URL}/v1/oauth2/token"
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en_US",
    }
    data = {"grant_type": "client_credentials"}
    auth = (settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET)

    try:
        response = requests.post(auth_url, headers=headers, data=data, auth=auth)
        response.raise_for_status()
        return response.json()["access_token"]
    except requests.exceptions.RequestException as e:
        error_response = e.response.text if e.response else "Keine Antwort erhalten."
        logger.error(
            "Fehler beim Abrufen des PayPal Access Tokens: %s",
            error_response,
            exc_info=True,
        )
        raise Exception("Konnte PayPal Access Token nicht abrufen.")


@csrf_exempt
def create_paypal_order(request):
    if request.method != "POST":
        return JsonResponse({"error": "Ungültige Request-Methode"}, status=405)

    try:
        data = json.loads(request.body)
        anmeldung_id = data.get("anmeldung_id")

        if not anmeldung_id:
            logger.error("Anmeldungs-ID fehlt im Request-Body.")
            return JsonResponse({"error": "Anmeldungs-ID fehlt"}, status=400)

        anmeldung_obj = Anmeldung.objects.get(id=anmeldung_id)

        amount = "0.01"  # <- Hier ggf. dynamisch berechnen
        access_token = get_paypal_access_token()

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }

        order_data = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": "EUR",
                        "value": amount,
                    },
                    "description": f"Anmeldung für {anmeldung_obj.vorname} {anmeldung_obj.nachname} - {anmeldung_obj.termin}",
                }
            ],
            "application_context": {
                "return_url": "https://deine-website.com/anmeldung-erfolgreich/",
                "cancel_url": "https://deine-website.com/anmeldung-abgebrochen/",
            },
        }

        response = requests.post(
            f"{settings.PAYPAL_API_BASE_URL}/v2/checkout/orders",
            headers=headers,
            json=order_data,
        )
        response.raise_for_status()

        order_data = response.json()
        anmeldung_obj.paypal_order_id = order_data["id"]
        anmeldung_obj.save()

        return JsonResponse({"id": order_data["id"]})

    except Anmeldung.DoesNotExist:
        return JsonResponse({"error": "Anmeldung nicht gefunden"}, status=404)
    except json.JSONDecodeError:
        logger.error("Ungültiges JSON im Request-Body.", exc_info=True)
        return JsonResponse({"error": "Ungültiges JSON"}, status=400)
    except requests.exceptions.RequestException as e:
        error = e.response.json() if e.response and e.response.content else str(e)
        logger.error("PayPal API Fehler: %s", error, exc_info=True)
        return JsonResponse({"error": str(error)}, status=500)
    except Exception as e:
        logger.critical("Unerwarteter Fehler: %s", e, exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def capture_paypal_order(request):
    if request.method != "POST":
        return JsonResponse({"error": "Ungültige Request-Methode"}, status=405)

    try:
        data = json.loads(request.body)
        order_id = data.get("orderID")

        if not order_id:
            return JsonResponse({"error": "Order ID ist erforderlich"}, status=400)

        try:
            anmeldung_obj = Anmeldung.objects.get(paypal_order_id=order_id)
        except Anmeldung.DoesNotExist:
            return JsonResponse({"error": "Anmeldung nicht gefunden"}, status=404)
        except Anmeldung.MultipleObjectsReturned:
            return JsonResponse({"error": "Mehrfache Anmeldungen gefunden"}, status=500)

        access_token = get_paypal_access_token()

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }

        capture_url = (
            f"{settings.PAYPAL_API_BASE_URL}/v2/checkout/orders/{order_id}/capture"
        )
        response = requests.post(capture_url, headers=headers)
        response.raise_for_status()

        capture_data = response.json()

        status = capture_data.get("status")
        payment_source = "paypal"
        ps = capture_data.get("payment_source", {})

        if "card" in ps:
            payment_source = "kreditkarte"
        elif "bank_account" in ps:
            payment_source = "sepa"

        if status == "COMPLETED":
            anmeldung_obj.ist_bezahlt = True
            anmeldung_obj.bezahlmethode = payment_source
            anmeldung_obj.zahlungsdatum = timezone.now()

            token = uuid.uuid4()  # Für DB (UUIDField)
            qr_string = str(token)

            participant, created = Participant.objects.get_or_create(
                anmeldung=anmeldung_obj,
                defaults={
                    "name": f"{anmeldung_obj.vorname} {anmeldung_obj.nachname}",
                    "email": anmeldung_obj.email,
                    "qr_code_token": token,
                },
            )

            if not created:
                participant.qr_code_token = token
                participant.save()

            qr_img = generate_qr_code(qr_string)  # Lesbare Daten im QR
            qr_url = upload_qr_to_supabase(str(participant.id), qr_img)

            anmeldung_obj.qr_code_url = qr_url
            anmeldung_obj.save()

            email_body = f"""
Hallo {anmeldung_obj.vorname},

vielen Dank für deine Anmeldung und die erfolgreiche Zahlung!

Hier ist dein QR-Code zur Teilnahme:
{qr_url}

Termin: {anmeldung_obj.termin}
Zahlungsdatum: {anmeldung_obj.zahlungsdatum.strftime('%d.%m.%Y %H:%M')}

Viele Grüße,
Dein Team
"""
            send_mail(
                subject="Anmeldebestätigung & QR-Code",
                message=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[anmeldung_obj.email],
                fail_silently=False,
            )

        return JsonResponse(
            {
                "id": capture_data.get("id"),
                "status": status,
                "bezahlmethode": payment_source,
            }
        )

    except json.JSONDecodeError:
        logger.error("Ungültiges JSON im Request-Body.", exc_info=True)
        return JsonResponse({"error": "Ungültiges JSON"}, status=400)
    except requests.exceptions.RequestException as e:
        error = e.response.json() if e.response and e.response.content else str(e)
        logger.error("Fehler bei PayPal-Abschluss: %s", error, exc_info=True)
        return JsonResponse({"error": str(error)}, status=500)
    except Exception as e:
        logger.critical("Unerwarteter Fehler: %s", e, exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)
