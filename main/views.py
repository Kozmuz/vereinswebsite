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
from django.http import JsonResponse
from .models import Participant
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from main.utils.qr_code_utils import generate_qr_code, upload_qr_to_supabase


def validate_qr(request, token):
    try:
        participant = Participant.objects.get(qr_code_token=token)
        if participant.paid:
            return JsonResponse({"status": "valid", "name": participant.name})
        else:
            return JsonResponse({"status": "not_paid"})
    except Participant.DoesNotExist:
        return JsonResponse({"status": "invalid"})


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
            return render(request, "main/anmeldung.html", context)
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
            qr_data = f"https://vereinswebsite.onrender.com/checkin/{anmeldung_obj.qr_code_token}"  # oder id, wenn du noch kein token hast
            qr_img = generate_qr_code(qr_data)
            qr_url = upload_qr_to_supabase(anmeldung_obj.id, qr_img)

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
                request, "main/checkin_invalid.html", {"grund": "Anmeldung nicht bezahlt"}
            )

    except Anmeldung.DoesNotExist:
        return render(
            request, "main/checkin_invalid.html", {"grund": "Anmeldung nicht gefunden"}
        )


from supabase import create_client, Client
