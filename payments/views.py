import json
import requests
import logging
import datetime
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from main.utils.qr_code_utils import generate_qr_code, upload_qr_to_supabase
from django.core.mail import send_mail
from django.shortcuts import render

from main.models import Anmeldung

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
        error_response_text = (
            e.response.text if e.response else "Keine Antwort erhalten."
        )
        logger.error(
            f"Fehler beim Abrufen des PayPal Access Tokens: {error_response_text}",
            exc_info=True,
        )
        raise Exception("Konnte PayPal Access Token nicht abrufen.")


@csrf_exempt
def create_paypal_order(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            anmeldung_id = data.get("anmeldung_id")

            if not anmeldung_id:
                logger.error("Anmeldungs-ID fehlt im Request-Body.")
                return JsonResponse({"error": "Anmeldungs-ID fehlt"}, status=400)

            try:
                anmeldung_obj = Anmeldung.objects.get(id=anmeldung_id)
            except Anmeldung.DoesNotExist:
                logger.error(f"Anmeldung mit ID {anmeldung_id} nicht gefunden.")
                return JsonResponse({"error": "Anmeldung nicht gefunden"}, status=404)

            calculated_amount = "0.01"
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
                            "value": calculated_amount,
                        },
                        "description": f"Anmeldung für {anmeldung_obj.vorname} {anmeldung_obj.nachname} - {anmeldung_obj.termin}",
                    }
                ],
                "application_context": {
                    "return_url": "https://deine-website.com/anmeldung-erfolgreich/",
                    "cancel_url": "https://deine-website.com/anmeldung-abgebrochen/",
                },
            }

            create_order_url = f"{settings.PAYPAL_API_BASE_URL}/v2/checkout/orders"
            response = requests.post(create_order_url, headers=headers, json=order_data)
            response.raise_for_status()

            paypal_order_data = response.json()
            order_id = paypal_order_data["id"]

            anmeldung_obj.paypal_order_id = order_id
            anmeldung_obj.save()

            return JsonResponse({"id": order_id})

        except json.JSONDecodeError:
            logger.error("Ungültiges JSON im Request-Body.", exc_info=True)
            return JsonResponse({"error": "Ungültiges JSON"}, status=400)
        except requests.exceptions.RequestException as e:
            error_details = (
                e.response.json() if e.response and e.response.content else str(e)
            )
            logger.error(f"PayPal API Fehler: {error_details}", exc_info=True)
            return JsonResponse({"error": str(error_details)}, status=500)
        except Exception as e:
            logger.critical(f"Unerwarteter Fehler: {e}", exc_info=True)
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Ungültige Request-Methode"}, status=405)


@csrf_exempt
def capture_paypal_order(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            order_id = data.get("orderID")

            if not order_id:
                logger.error("Order ID fehlt.")
                return JsonResponse({"error": "Order ID ist erforderlich"}, status=400)

            try:
                anmeldung_obj = Anmeldung.objects.get(paypal_order_id=order_id)
            except Anmeldung.DoesNotExist:
                logger.error(f"Anmeldung mit Order ID {order_id} nicht gefunden.")
                return JsonResponse({"error": "Anmeldung nicht gefunden"}, status=404)
            except Anmeldung.MultipleObjectsReturned:
                logger.error(f"Mehrfache Anmeldungen für Order ID {order_id}")
                return JsonResponse(
                    {"error": "Mehrfache Anmeldungen gefunden"}, status=500
                )

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

            paypal_capture_data = response.json()
            payment_status = paypal_capture_data.get("status", None)

            payment_source = "paypal"
            try:
                ps = paypal_capture_data.get("payment_source", {})
                if "card" in ps:
                    payment_source = "kreditkarte"
                elif "bank_account" in ps:
                    payment_source = "sepa"
            except (KeyError, IndexError):
                pass

            logger.info(
                f"Zahlung abgeschlossen. Status: {payment_status}, Methode: {payment_source}"
            )

            if payment_status == "COMPLETED":
                anmeldung_obj.ist_bezahlt = True
                anmeldung_obj.bezahlmethode = payment_source
                anmeldung_obj.zahlungsdatum = datetime.datetime.now()

                qr_data = f"Name: {anmeldung_obj.vorname} {anmeldung_obj.nachname}, Termin: {anmeldung_obj.termin}"
                qr_img = generate_qr_code(qr_data)
                qr_url = upload_qr_to_supabase(anmeldung_obj.id, qr_img)
                anmeldung_obj.qr_code_url = qr_url
                anmeldung_obj.save()

                email_body = f"""
Hallo {anmeldung_obj.vorname},

vielen Dank für deine Anmeldung und die erfolgreiche Zahlung!

Hier ist dein QR-Code zur Teilnahme (z.B. für den Check-in):
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
                    "id": paypal_capture_data.get("id"),
                    "status": payment_status,
                    "bezahlmethode": payment_source,
                }
            )

        except json.JSONDecodeError:
            logger.error("Ungültiges JSON im Request-Body.", exc_info=True)
            return JsonResponse({"error": "Ungültiges JSON"}, status=400)
        except requests.exceptions.RequestException as e:
            error_details = (
                e.response.json() if e.response and e.response.content else str(e)
            )
            logger.error(f"Fehler bei PayPal-Abschluss: {error_details}", exc_info=True)
            return JsonResponse({"error": str(error_details)}, status=500)
        except Exception as e:
            logger.critical(f"Unerwarteter Fehler: {e}", exc_info=True)
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Ungültige Request-Methode"}, status=405)
