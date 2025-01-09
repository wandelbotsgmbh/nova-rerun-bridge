import wandelbots_api_client as wb
import requests
from decouple import config

CELL_ID = config("CELL_ID", default="cell", cast=str)


def get_api_client() -> wb.ApiClient:
    """Creates a new API client for the wandelbots API."""
    access_token = config("NOVA_ACCESS_TOKEN", default=None, cast=str)

    base_url = get_base_url()
    client_config = wb.Configuration(host=base_url)
    client_config.verify_ssl = False

    if access_token:
        client_config.access_token = access_token

    return wb.ApiClient(client_config)


def get_base_url() -> str:
    # in-cluster it is the api-gateway service
    # when working with a remote instance one needs to provide the host via env variable
    api_host = config(
        "WANDELAPI_BASE_URL", default="api-gateway.wandelbots.svc.cluster.local:8080", cast=str
    )
    api_host = api_host.strip()
    api_host = api_host.replace("http://", "")
    api_host = api_host.replace("https://", "")
    api_host = api_host.rstrip("/")
    api_base_path = "/api/v1"
    protocol = get_protocol(api_host)
    if protocol is None:
        msg = f"Could not determine protocol for host {api_host}. Make sure the host is reachable."
        raise Exception(msg)
    return f"{protocol}{api_host}{api_base_path}"


# get the protocol of the host (http or https)
def get_protocol(host) -> str:
    api = f"/api/v1/cells/{CELL_ID}/controllers"
    headers = {}
    access_token = config("NOVA_ACCESS_TOKEN", default=None, cast=str)
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    try:
        response = requests.get(f"https://{host}{api}", headers=headers, timeout=5)
        if response.status_code == 200:
            return "https://"
    except requests.RequestException:
        pass

    try:
        response = requests.get(f"http://{host}{api}", headers=headers, timeout=5)
        if response.status_code == 200:
            return "http://"
    except requests.RequestException:
        pass

    return None
