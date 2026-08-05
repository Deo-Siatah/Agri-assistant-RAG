import requests


class SoilServiceError(Exception):

    pass


def get_soil_data(lat: float, lon: float) -> dict:

    url = (
        "https://rest.isric.org/soilgrids/v2.0/properties/query"
        f"?lon={lon}"
        f"&lat={lat}"
        "&property=phh2o"
        "&property=nitrogen"
        "&property=soc"
        "&property=clay"
        "&property=sand"
        "&property=silt"
        "&depth=0-5cm"
        "&value=mean"
    )

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError) as exc:
        raise SoilServiceError(
            "Failed to fetch soil data from SoilGrids."
        ) from exc