# main/utils/qr_code_utils.py

import qrcode
from io import BytesIO
from supabase import create_client
from django.conf import settings
import datetime
import tempfile

# Supabase Initialisierung
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


def generate_qr_code_url(token: str) -> str:
    # Einfacher Return, kann bei Bedarf angepasst werden
    return token


def generate_qr_code(data: str) -> BytesIO:
    """Erzeugt ein QR-Code PNG-Bild als BytesIO-Objekt."""
    qr = qrcode.make(data)
    byte_io = BytesIO()
    qr.save(byte_io, format="PNG")
    byte_io.seek(0)
    return byte_io


def upload_qr_to_supabase(participant_token: str, qr_image: BytesIO) -> str:
    """Lädt das QR-Code-Bild zu Supabase hoch und gibt die öffentliche URL zurück."""
    timestamp = datetime.datetime.now().isoformat()
    filename = f"qr_codes/{participant_token}_{timestamp}.png"

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        temp_file.write(qr_image.getvalue())
        temp_file.flush()

        response = supabase.storage.from_("qrcodes").upload(
            filename, temp_file.name, {"content-type": "image/png"}
        )

    if hasattr(response, "error") and response.error is not None:
        raise Exception(f"Upload fehlgeschlagen: {response.error}")

    return f"{settings.SUPABASE_URL}/storage/v1/object/public/qrcodes/{filename}"
