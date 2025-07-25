"""
Django settings for verein project.

Generated by 'django-admin startproject' using Django 5.2.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

import os
import dj_database_url  # for simplified DB connections - JK
from decouple import config  # Importiere config von decouple
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-v(ka$lr(c2qq@drkk$$4rg#ths8o7_@6$db(4f#lmz9t^kn1!p"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [".onrender.com", "localhost", "127.0.0.1"]
# import psycopg2 # Dieser Import ist hier nicht direkt notwendig, dj_database_url handhabt das.


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "website",
    "payments",
    "main",  # Stelle sicher, dass 'main' hier korrekt eingetragen ist für dein Anmeldungs-Modell
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Nur einmal! Diese Zeile sollte die einzige sein
]


ROOT_URLCONF = "verein.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",  # Sicherstellen, dass debug enthalten ist, wenn du das verwenden möchtest
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "verein.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": dj_database_url.config(
        default=config("DATABASE_URL"), conn_max_age=600, ssl_require=True
    )
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# PayPal-Einstellungen
# Die folgenden Zeilen sind die korrekte Definition und ersetzen die doppelten am Anfang
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")

# Neu: PayPal Modus (z.B. 'sandbox' oder 'live')
PAYPAL_MODE = os.getenv("PAYPAL_MODE", "sandbox")  # Standardwert ist 'sandbox'

if PAYPAL_MODE == "live":
    PAYPAL_API_BASE_URL = "https://api-m.paypal.com"
else:  # Default to sandbox
    PAYPAL_API_BASE_URL = "https://api-m.sandbox.paypal.com"


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "de-de"  # Auf Deutsch geändert, da du deutsche Kommentare verwendest

TIME_ZONE = "Europe/Berlin"  # Auf Zeitzone für Deutschland geändert

USE_I18N = True

USE_TZ = True  # Stelle sicher, dass die Datenbank auch UTC verwendet oder konvertiert

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Wenn du Media-Dateien verwendest, dann auch das hier:
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "maganiac13@gmail.com"
EMAIL_HOST_PASSWORD = "iksh glzi tnwo qjco"  # Achtung: Kein normales Passwort!
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

VALIDATE_BASE_URL = "https://vereinswebsite.onrender.com"
