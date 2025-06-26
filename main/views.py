import re
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from .forms import Anmeldeformular
from .models import Anmeldung, Participant
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.urls import reverse
import json
from datetime import datetime
from main.utils.qr_code_utils import (
    generate_qr_code,
    upload_qr_to_supabase,
    generate_qr_code_url,
)


def qr_scanner_view(request):
    return render(request, "main/qr_scanner.html")


def validate_qr(request, token):
    if not re.match(r"^[0-9a-fA-F\-]{36}$", token):
        return render(
            request, "main/checkin_invalid.html", {"grund": "Ungültiges Token-Format"}
        )

    try:
        participant = Participant.objects.get(qr_code_token=str(token))
        return render(request, "main/checkin_valid.html", {"participant": participant})
    except Participant.DoesNotExist:
        grund = f"Ungültiger QR-Code: Teilnehmer mit Token '{token}' nicht gefunden."
        return render(request, "main/checkin_invalid.html", {"grund": grund})


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

            participant = Participant.objects.create(
                name=f"{anmeldung_obj.vorname} {anmeldung_obj.nachname}",
                email=anmeldung_obj.email,
                anmeldung=anmeldung_obj,  # neu
            )

            context = {
                "form": form,
                "anmeldung_id": participant.id,  # Nutze die ID vom Participant!
                "PAYPAL_CLIENT_ID": settings.PAYPAL_CLIENT_ID,
            }
            return redirect(
                f"{reverse('anmeldung_erfolg')}?anmeldung_id={participant.id}"
            )
    else:
        form = Anmeldeformular()

    context = {"form": form, "PAYPAL_CLIENT_ID": settings.PAYPAL_CLIENT_ID}
    return render(request, "main/anmeldung.html", context)


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


def zahlung_bestaetigen_view(request):
    anmeldung_id = request.GET.get("anmeldung_id")

    if not anmeldung_id:
        return HttpResponse("Ungültige Anmeldung", status=400)

    participant = get_object_or_404(Participant, id=anmeldung_id)

    if not participant.paid:
        participant.paid = True
        participant.save()

        # Auch die Anmeldung als bezahlt markieren
        if participant.anmeldung:
            anmeldung = participant.anmeldung
            anmeldung.ist_bezahlt = True
            anmeldung.zahlungsdatum = datetime.now()

            # QR-Code generieren & hochladen
            anmeldung_obj = anmeldung
            qr_data = f"ID: {anmeldung_obj.id}, Name: {anmeldung_obj.vorname} {anmeldung_obj.nachname}, Termin: {anmeldung_obj.termin}"
            qr_img = generate_qr_code(qr_data)
            qr_url = upload_qr_to_supabase(participant.qr_code_token, qr_img)

            # URL in DB speichern
            anmeldung_obj.qr_code_url = qr_url
            anmeldung_obj.save()

            # ✅ E-Mail senden
            email_body = f"""
Hallo {anmeldung.vorname},

vielen Dank für deine Anmeldung und die erfolgreiche Zahlung!

Hier ist dein QR-Code zur Teilnahme:
{qr_url}

Termin: {anmeldung.termin}
Zahlungsdatum: {anmeldung.zahlungsdatum.strftime('%d.%m.%Y %H:%M')}

Viele Grüße,
Dein Team
"""
            send_mail(
                subject="Anmeldebestätigung & QR-Code",
                message=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[anmeldung.email],
                fail_silently=False,
            )

    return HttpResponse("Bezahlung bestätigt. QR-Code wurde per E-Mail verschickt.")


def qr_checkin_view(request, anmeldung_id):
    try:
        anmeldung = Anmeldung.objects.get(id=anmeldung_id)

        if anmeldung.ist_bezahlt:
            return render(request, "main/checkin_valid.html", {"anmeldung": anmeldung})
        else:
            return render(
                request,
                "main/checkin_invalid.html",
                {"grund": "Anmeldung nicht bezahlt"},
            )

    except Anmeldung.DoesNotExist:
        return render(
            request, "main/checkin_invalid.html", {"grund": "Anmeldung nicht gefunden"}
        )
