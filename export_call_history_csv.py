import os
import csv
import time
from datetime import datetime
import requests
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_ID = os.getenv("ZOOM_ACCOUNT_ID")
CLIENT_ID = os.getenv("ZOOM_CLIENT_ID")
CLIENT_SECRET = os.getenv("ZOOM_CLIENT_SECRET")
MANUAL_TOKEN = os.getenv("ZOOM_BEARER_TOKEN")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "data")

BASE_API_URL = "https://api.zoom.us/v2"


def get_access_token() -> str:
    """Obtiene o renueva el token mediante Server-to-Server OAuth."""
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


def flatten_record(record: dict) -> dict:
    """
    Aplana diccionarios anidados o listas simples para que 
    se almacenen limpiamente en columnas de un archivo CSV.
    """
    flat = {}
    for key, value in record.items():
        if isinstance(value, dict):
            for sub_key, sub_val in value.items():
                flat[f"{key}_{sub_key}"] = sub_val
        elif isinstance(value, list):
            flat[key] = "; ".join(str(v) for v in value)
        else:
            flat[key] = value
    return flat


def export_all_call_history_to_csv(from_date: str = None, to_date: str = None):
    token = get_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    endpoint = f"{BASE_API_URL}/phone/call_history"
    all_rows = []
    all_fieldnames = set()
    next_page_token = None
    page = 1

    print("[*] Iniciando extracción de registros de llamadas...")

    while True:
        params = {
            "page_size": 300  # Máximo por llamada para minimizar peticiones
        }
        if next_page_token:
            params["next_page_token"] = next_page_token
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date

        response = requests.get(endpoint, headers=headers, params=params, timeout=25)

        # Manejo preventivo del Rate Limit (HTTP 429)
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 5))
            print(f"[!] Rate limit alcanzado. Pausando por {retry_after} segundos...")
            time.sleep(retry_after)
            continue

        if response.status_code != 200:
            print(f"[X] Error en la petición: {response.status_code}")
            print(response.text)
            response.raise_for_status()

        data = response.json()
        batch = data.get("call_history", [])

        for item in batch:
            flat_item = flatten_record(item)
            all_fieldnames.update(flat_item.keys())
            all_rows.append(flat_item)

        print(f"    -> Página {page}: {len(batch)} registros procesados (Total: {len(all_rows)})")

        next_page_token = data.get("next_page_token")
        if not next_page_token:
            break

        page += 1
        time.sleep(0.25)

    if not all_rows:
        print("[!] No se encontraron registros para exportar.")
        return

    # Asegura la existencia de la carpeta de salida
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Genera el nombre del archivo dentro del directorio de salida
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(OUTPUT_DIR, f"call_history_{timestamp_str}.csv")

    # Escribir el archivo CSV ordenando las columnas
    fieldnames_ordered = sorted(list(all_fieldnames))
    with open(filename, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames_ordered)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\n[✓] Extracción finalizada con éxito.")
    print(f"[✓] Se guardaron {len(all_rows)} registros en el archivo: {filename}")


if __name__ == "__main__":
    f_from = os.getenv("MANUAL_FROM")
    f_to = os.getenv("MANUAL_TO")

    if f_from and f_to:
        print(f"[*] Filtro aplicado: {f_from} al {f_to}")
        export_all_call_history_to_csv(from_date=f_from, to_date=f_to)
    else:
        print("[*] Sin rango manual detectado. Usando corte por defecto de Zoom...")
        export_all_call_history_to_csv()