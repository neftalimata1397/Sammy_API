import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_ID = os.getenv("ZOOM_ACCOUNT_ID")
CLIENT_ID = os.getenv("ZOOM_CLIENT_ID")
CLIENT_SECRET = os.getenv("ZOOM_CLIENT_SECRET")
MANUAL_TOKEN = os.getenv("ZOOM_BEARER_TOKEN")

BASE_API_URL = "https://api.zoom.us/v2"


def get_access_token() -> str:
    """Genera o recupera el token de acceso."""
    if MANUAL_TOKEN and MANUAL_TOKEN.strip():
        return MANUAL_TOKEN.strip()

    if not all([ACCOUNT_ID, CLIENT_ID, CLIENT_SECRET]):
        raise ValueError("Faltan credenciales en el archivo .env")

    url = "https://zoom.us/oauth/token"
    params = {
        "grant_type": "account_credentials",
        "account_id": ACCOUNT_ID
    }
    
    response = requests.post(
        url,
        params=params,
        auth=(CLIENT_ID, CLIENT_SECRET),
        timeout=15
    )
    response.raise_for_status()
    return response.json()["access_token"]


def get_single_call():
    """Consulta la API de Zoom Phone pidiendo únicamente un registro."""
    token = get_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    endpoint = f"{BASE_API_URL}/phone/call_history"
    
    # page_size=1 limita la respuesta al primer registro
    params = {
        "page_size": 1
    }

    print("[*] Consultando una sola llamada de prueba...")
    response = requests.get(endpoint, headers=headers, params=params, timeout=15)
    
    if response.status_code != 200:
        print(f"[!] Error: {response.status_code}")
        print(response.text)
        return

    data = response.json()
    call_list = data.get("call_history", [])

    if not call_list:
        print("[!] No se encontraron registros de llamadas en la cuenta.")
        return

    # Extraemos el primer y único elemento devuelto
    single_call = call_list[0]

    # Imprimir en terminal con formato legible
    print("\n--- Estructura del registro obtenido ---")
    print(json.dumps(single_call, indent=2, ensure_ascii=False))

    # Guardar en un JSON local para análisis
    with open("single_call_sample.json", "w", encoding="utf-8") as f:
        json.dump(single_call, f, indent=2, ensure_ascii=False)

    print("\n[✓] Muestra guardada exitosamente en 'single_call_sample.json'.")


if __name__ == "__main__":
    try:
        get_single_call()
    except Exception as e:
        print(f"[X] Ocurrió un error: {e}")