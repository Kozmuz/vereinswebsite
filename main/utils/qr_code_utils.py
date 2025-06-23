import qrcode
from io import BytesIO
from supabase import create_client
from django.conf import settings
import datetime
import base64

# Supabase Initialisierung
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


def generate_qr_code(data: str) -> BytesIO:
    qr = qrcode.make(data)
    byte_io = BytesIO()
    qr.save(byte_io, format="PNG")
    byte_io.seek(0)
    return byte_io


def upload_qr_to_supabase(anmeldung_id: int, qr_image: BytesIO) -> str:
    filename = (
        f"qr_codes/anmeldung_{anmeldung_id}_{datetime.datetime.now().isoformat()}.png"
    )
    response = supabase.storage.from_("public").upload(
        filename, qr_image, {"content-type": "image/png"}
    )
    if response.get("error"):
        raise Exception(f"Upload fehlgeschlagen: {response['error']['message']}")
    return f"{settings.SUPABASE_URL}/storage/v1/object/public/public/{filename}"
