import qrcode
from io import BytesIO
from supabase import create_client
from django.conf import settings
import datetime
import base64
import tempfile

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

    # Temporäre Datei anlegen und Inhalt schreiben
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        temp_file.write(qr_image.getvalue())
        temp_file.flush()  # sicherstellen, dass alles geschrieben wurde

        response = supabase.storage.from_("qrcodes").upload(
            filename, temp_file.name, {"content-type": "image/png"}
        )

    if hasattr(response, "error") and response.error is not None:
        raise Exception(f"Upload fehlgeschlagen: {response.error}")

    return f"{settings.SUPABASE_URL}/storage/v1/object/public/qrcodes/{filename}"