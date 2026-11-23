import cloudinary
import cloudinary.uploader
import cloudinary.api

from app.config import settings


def _parse_cloudinary_url(url: str) -> dict:
    # cloudinary://API_KEY:API_SECRET@CLOUD_NAME
    rest = url.split("://", 1)[-1]
    creds, _, cloud_name = rest.rpartition("@")
    api_key, _, api_secret = creds.partition(":")
    return {
        "cloud_name": cloud_name,
        "api_key": api_key,
        "api_secret": api_secret,
    }


def configure_cloudinary() -> bool:
    """Configure the Cloudinary SDK from settings/env. Returns True if set."""
    url = settings.cloudinary_url or None
    if url:
        cloudinary.config(**_parse_cloudinary_url(url), secure=True)
        return True
    if settings.cloudinary_cloud_name:
        cloudinary.config(cloud_name=settings.cloudinary_cloud_name, secure=True)
        return True
    return False


def _cloud_name() -> str:
    return getattr(cloudinary.config(), "cloud_name", "") or ""


def cloudinary_enabled() -> bool:
    return bool(_cloud_name())


def media_url(public_id: str, resource_type: str, transform: str = "") -> str:
    base = f"https://res.cloudinary.com/{_cloud_name()}/{resource_type}/upload"
    return f"{base}/{transform}{public_id}"
