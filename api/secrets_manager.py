import os
from typing import Optional

def get_secret_from_gcp(key: str) -> Optional[str]:
    """Busca a chave no Google Cloud Secret Manager usando o nome exato."""
    try:
        from google.cloud import secretmanager
        client = secretmanager.SecretManagerServiceClient()
        # Tenta o nome exato (Ex: GEMINI_API_KEY)
        name = f"projects/brasili-ia-news/secrets/{key}/versions/latest"
        response = client.access_secret_version(name=name)
        return response.payload.data.decode("UTF-8")
    except Exception:
        try:
            # Tenta a versão com hífens se falhar (Ex: gemini-api-key)
            secret_id = key.lower().replace("_", "-")
            name = f"projects/brasili-ia-news/secrets/{secret_id}/versions/latest"
            response = client.access_secret_version(name=name)
            return response.payload.data.decode("UTF-8")
        except Exception:
            return None

def get_secret(key: str, fallback: Optional[str] = None) -> Optional[str]:
    """
    Busca uma chave na Nuvem (GCP Secret Manager ou Env Vars).
    """
    gcp_val = get_secret_from_gcp(key)
    if gcp_val:
        return gcp_val

    env_val = os.getenv(key)
    if env_val:
        return env_val

    return fallback
