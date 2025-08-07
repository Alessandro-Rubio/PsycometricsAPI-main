from pathlib import Path
from decouple import config
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('DJANGO_SECRET_KEY')
DEBUG = True 

# ALLOWED_HOSTS = [
#     "localhost",
#     "127.0.0.1",
#     "192.168.100.73",
#     "18.206.182.194",
#     "psycometrics.app",
#     "www.psycometrics.app",
# ]

ALLOWED_HOSTS = [
    "*",  # Allow all hosts for development purposes
]

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'rest_framework',
    'rest_framework.authtoken',
    'PsycometricsAPI',
    'corsheaders',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'PsycometricsAI.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'PsycometricsAI.wsgi.application'

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "PsycometricsAPI.authentication.CustomJwtAuthentication.CustomJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
}

CORS_ALLOW_ALL_ORIGINS = True

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(weeks=1),  # Access token lasts 1 week
    "REFRESH_TOKEN_LIFETIME": timedelta(weeks=2),  # Refresh token lasts 2 weeks
    "ROTATE_REFRESH_TOKENS": False,  # Optional: Set to True if you want to rotate refresh tokens
    "BLACKLIST_AFTER_ROTATION": True,  # Optional: Blacklist old refresh tokens after rotation
}

MICROSOFT_AUTH_CLIENT_ID = config('MICROSOFT_CLIENT_ID')
MICROSOFT_AUTH_CLIENT_SECRET = config('MICROSOFT_CLIENT_SECRET')
AZURE_STORAGE_CONNECTION_STRING = config("AZURE_STORAGE_CONNECTION_STRING")
AZURE_STORAGE_CONTAINER_NAME = config("AZURE_STORAGE_CONTAINER_NAME")