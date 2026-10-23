import os
import csv
import time
from datetime import datetime, date, timedelta
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
    if MANUAL_TOKEN and MANUAL_TOKEN.strip():
        return MANUAL_TOKEN.strip()

    if not all([ACCOUNT_ID, CLIENT_ID, CLIENT_SECRET]):
        raise ValueError("Faltan credenciales en las variables de entorno o archivo .env")

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


def get_previous_month_range() -> tuple[str, str]:
    """Calcula el primer y último día del mes anterior."""
    today = date.today()
    first_of_this_month = today.replace(day=1)
    last_of_prev_month = first_of_this_month - timedelta(days=1)
    first_of_prev_month = last_of_prev_month.replace(day=1)
    return first_of_prev_month.strftime("%Y-%m-%d"), last_of_prev_month.strftime("%Y-%m-%d")


def flatten_record(record: dict) -> dict:
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


def export_call_history(from_date: str, to_date: str):
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

    print(f"[*] Consultando periodo de Zoom Phone: {from_date} al {to_date}")

    while True:
        params = {
            "page_size": 300,
            "from": from_date,
            "to": to_date
        }
        if next_page_token:
            params["next_page_token"] = next_page_token

        response = requests.get(endpoint, headers=headers, params=params, timeout=25)

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 5))
            print(f"[!] Rate limit alcanzado. Pausando {retry_after}s...")
            time.sleep(retry_after)
            continue

        if response.status_code != 200:
            print(f"[X] Error en API: {response.status_code}\n{response.text}")
            response.raise_for_status()

        data = response.json()
        batch = data.get("call_history", [])

        for item in batch:
            flat_item = flatten_record(item)
            all_fieldnames.update(flat_item.keys())
            all_rows.append(flat_item)

        print(f"    -> Lote {page}: {len(batch)} registros (Total: {len(all_rows)})")

        next_page_token = data.get("next_page_token")
        if not next_page_token:
            break

        page += 1
        time.sleep(0.25)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = os.path.join(OUTPUT_DIR, f"call_history_{from_date}_al_{to_date}.csv")

    if not all_rows:
        print("[!] No hubo llamadas registradas en este periodo.")
        return

    fieldnames_ordered = sorted(list(all_fieldnames))
    with open(filename, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames_ordered)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"[✓] Archivo generado exitosamente en: {filename}")


if __name__ == "__main__":
    # Si se definen FROM_DATE y TO_DATE en el .env las respeta, si no, toma el mes anterior automático
    custom_from = os.getenv("FROM_DATE")
    custom_to = os.getenv("TO_DATE")

    if custom_from and custom_to:
        f_start, f_end = custom_from, custom_to
    else:
        f_start, f_end = get_previous_month_range()

    export_call_history(f_start, f_end)