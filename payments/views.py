import json
import requests
import logging
import datetime  # Für das Speichern des Zahlungsdatums

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import (
    csrf_exempt,
)  # Temporär für Tests - FÜR PRODUKTION ENTFERNEN!
from django.conf import settings

# Importiere dein Anmeldungs-Modell. Passe 'main' an den tatsächlichen App-Namen an,
# in dem dein Anmeldung-Modell definiert ist (z.B. 'website.models' oder 'anmeldung.models').
from main.models import Anmeldung  # Beispiel-Import

logger = logging.getLogger(__name__)

from django.shortcuts import render


def anmeldung_erfolg_view(request):
    return render(request, "anmeldung_erfolg.html")


# Django view für den Stripe-Checkout (existierte bereits)
def checkout(request):
    return HttpResponse("Hier kommt später das Stripe-Bezahlformular.")


# Hilfsfunktion, um einen PayPal Access Token zu erhalten
def get_paypal_access_token():
    auth_url = f"{settings.PAYPAL_API_BASE_URL}/v1/oauth2/token"
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en_US",
    }
    data = {"grant_type": "client_credentials"}
    # Authentifizierung mit Client ID und Secret aus settings.py
    auth = (settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET)

    try:
        response = requests.post(auth_url, headers=headers, data=data, auth=auth)
        response.raise_for_status()  # Löst HTTPError für schlechte Antworten (4xx oder 5xx) aus
        return response.json()["access_token"]
    except requests.exceptions.RequestException as e:
        # Detaillierte Fehlermeldung loggen
        error_response_text = (
            e.response.text if e.response else "Keine Antwort erhalten."
        )
        logger.error(
            f"Fehler beim Abrufen des PayPal Access Tokens: {error_response_text}",
            exc_info=True,
        )
        raise Exception("Konnte PayPal Access Token nicht abrufen.")


def create_paypal_order(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            # Annahme: Frontend sendet die ID der bereits gespeicherten Anmeldung
            anmeldung_id = data.get("anmeldung_id")

            if not anmeldung_id:
                logger.error(
                    "Anmeldungs-ID fehlt im Request-Body für create_paypal_order."
                )
                return JsonResponse({"error": "Anmeldungs-ID fehlt"}, status=400)

            try:
                anmeldung_obj = Anmeldung.objects.get(id=anmeldung_id)
            except Anmeldung.DoesNotExist:
                logger.error(
                    f"Anmeldung mit ID {anmeldung_id} nicht gefunden für PayPal Order Erstellung."
                )
                return JsonResponse({"error": "Anmeldung nicht gefunden"}, status=404)

            calculated_amount = "10.00"
            logger.info(
                f"Erstelle PayPal Order für Anmeldung {anmeldung_id} mit Betrag: {calculated_amount} EUR."
            )

            access_token = get_paypal_access_token()

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
            }
            order_data = {
                "intent": "CAPTURE",  # Zahlungsabsicht: Direkt erfassen
                "purchase_units": [
                    {
                        "amount": {
                            "currency_code": "EUR",  # Währung
                            "value": calculated_amount,  # Der auf dem Backend ermittelte Betrag
                        },
                        "description": f"Anmeldung für {anmeldung_obj.vorname} {anmeldung_obj.nachname} - {anmeldung_obj.termin}",
                    }
                ],
                "application_context": {
                    "return_url": "https://deine-website.com/anmeldung-erfolgreich/",  # Passe dies an deine Erfolgsseite an
                    "cancel_url": "https://deine-website.com/anmeldung-abgebrochen/",  # Passe dies an deine Abbruchseite an
                },
            }

            create_order_url = f"{settings.PAYPAL_API_BASE_URL}/v2/checkout/orders"
            response = requests.post(create_order_url, headers=headers, json=order_data)
            response.raise_for_status()  # Prüft auf HTTP-Fehler (4xx/5xx)

            paypal_order_data = response.json()
            order_id = paypal_order_data["id"]

            # Speichere die PayPal Order ID in der Anmeldung, um sie später zu referenzieren
            anmeldung_obj.paypal_order_id = order_id
            anmeldung_obj.save()
            logger.info(
                f"PayPal Order {order_id} erfolgreich für Anmeldung {anmeldung_id} erstellt."
            )

            return JsonResponse({"id": order_id})

        except json.JSONDecodeError:
            logger.error(
                "Ungültiges JSON im Request-Body für create_paypal_order.",
                exc_info=True,
            )
            return JsonResponse(
                {"error": "Ungültiges JSON im Request-Body"}, status=400
            )
        except requests.exceptions.RequestException as e:
            # Fehler bei der Kommunikation mit der PayPal API
            error_details = (
                e.response.json() if e.response and e.response.content else str(e)
            )
            logger.error(
                f"PayPal API Fehler beim Erstellen der Bestellung: {error_details}",
                exc_info=True,
            )
            return JsonResponse(
                {"error": f"Fehler bei der PayPal-Bestellung: {error_details}"},
                status=500,
            )
        except Exception as e:
            # Unerwarteter Fehler
            logger.critical(
                f"Ein unerwarteter Fehler ist aufgetreten in create_paypal_order: {e}",
                exc_info=True,
            )
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Ungültige Request-Methode"}, status=405)


def capture_paypal_order(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            order_id = data.get("orderID")

            if not order_id:
                logger.error("Order ID fehlt im Request-Body für capture_paypal_order.")
                return JsonResponse({"error": "Order ID ist erforderlich"}, status=400)

            try:
                anmeldung_obj = Anmeldung.objects.get(paypal_order_id=order_id)
            except Anmeldung.DoesNotExist:
                logger.error(
                    f"Anmeldung nicht gefunden für PayPal Order ID: {order_id}."
                )
                return JsonResponse(
                    {"error": "Anmeldung für diese Bestellung nicht gefunden"},
                    status=404,
                )
            except Anmeldung.MultipleObjectsReturned:
                logger.error(
                    f"Mehrere Anmeldungen gefunden für PayPal Order ID: {order_id}."
                )
                return JsonResponse(
                    {
                        "error": "Interner Fehler: Mehrere Anmeldungen mit derselben PayPal Order ID."
                    },
                    status=500,
                )

            access_token = get_paypal_access_token()

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
            }

            capture_order_url = (
                f"{settings.PAYPAL_API_BASE_URL}/v2/checkout/orders/{order_id}/capture"
            )
            response = requests.post(capture_order_url, headers=headers)
            response.raise_for_status()

            paypal_capture_data = response.json()

            payment_status = paypal_capture_data.get("status", None)

            # Extrahiere Zahlungsmethode
            payment_source = "paypal"  # Default fallback
            try:
                capture = paypal_capture_data["purchase_units"][0]["payments"][
                    "captures"
                ][0]
                if "payment_source" in paypal_capture_data:
                    ps = paypal_capture_data["payment_source"]
                if "paypal" in ps:
                    payment_source = "paypal"
                elif "card" in ps:
                    payment_source = "kreditkarte"
                elif "bank_account" in ps:
                    payment_source = "sepa"

                    response = requests.post(capture_order_url, headers=headers)
                    response.raise_for_status()
                    paypal_capture_data = response.json()
                    payment_status = paypal_capture_data.get("status", None)

                # 2. Extra-Request: Hole vollständige Order-Details (inkl. Zahlungsmethode)
                order_details_url = (
                    f"{settings.PAYPAL_API_BASE_URL}/v2/checkout/orders/{order_id}"
                )
                order_response = requests.get(order_details_url, headers=headers)
                order_response.raise_for_status()
                order_data = order_response.json()

                # 3. Zahlungsmethode auslesen
                payment_source = "paypal"  # fallback
                ps = order_data.get("payment_source", {})
                if "paypal" in ps:
                    payment_source = "paypal"
                elif "card" in ps:
                    payment_source = "kreditkarte"
                elif "bank_account" in ps:
                    payment_source = "sepa"

            except (KeyError, IndexError):
                pass  # fallback auf "paypal"
            logger.info(
                f"PayPal Zahlung abgeschlossen. Status: {payment_status}, Zahlungsmethode: {payment_source}"
            )

            if payment_status == "COMPLETED":
                anmeldung_obj.ist_bezahlt = True
                anmeldung_obj.bezahlmethode = payment_source
                anmeldung_obj.zahlungsdatum = datetime.datetime.now()
                anmeldung_obj.save()

            return JsonResponse(
                {
                    "id": paypal_capture_data.get("id"),
                    "status": payment_status,
                    "bezahlmethode": payment_source,
                }
            )

        except json.JSONDecodeError:
            logger.error(
                "Ungültiges JSON im Request-Body für capture_paypal_order.",
                exc_info=True,
            )
            return JsonResponse(
                {"error": "Ungültiges JSON im Request-Body"}, status=400
            )
        except requests.exceptions.RequestException as e:
            error_details = (
                e.response.json() if e.response and e.response.content else str(e)
            )
            logger.error(
                f"PayPal API Fehler beim Abschließen der Bestellung: {error_details}",
                exc_info=True,
            )
            return JsonResponse(
                {
                    "error": f"Fehler beim Abschließen der PayPal-Bestellung: {error_details}"
                },
                status=500,
            )
        except Exception as e:
            logger.critical(
                f"Ein unerwarteter Fehler ist aufgetreten in capture_paypal_order: {e}",
                exc_info=True,
            )
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Ungültige Request-Methode"}, status=405)
