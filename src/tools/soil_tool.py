from src.services.soil_service import SoilServiceError, get_soil_data


class SoilTool:

    # TODO: add Redis caching here once src/cache/cache_utils.py exists
    def run(self, latitude, longitude):

        return get_soil_summary(latitude, longitude)


def get_soil_summary(lat: float, lon: float) -> dict:

    output_keys = {
        "phh2o": "ph",
        "nitrogen": "nitrogen",
        "soc": "organic_carbon",
        "clay": "clay_pct",
        "sand": "sand_pct",
        "silt": "silt_pct",
    }

    summary = {value: None for value in output_keys.values()}

    try:
        data = get_soil_data(lat, lon)
    except SoilServiceError:
        return summary

    layers = (((data or {}).get("properties") or {}).get("layers") or [])

    for layer in layers:

        layer_name = layer.get("name")
        output_key = output_keys.get(layer_name)

        if output_key is None:
            continue

        try:
            d_factor = layer["unit_measure"]["d_factor"]
            mean = layer["depths"][0]["values"]["mean"]
        except (KeyError, IndexError, TypeError):
            summary[output_key] = None
            continue

        if mean is None or d_factor in (None, 0):
            summary[output_key] = None
            continue

        try:
            summary[output_key] = float(mean) / float(d_factor)
        except (TypeError, ValueError, ZeroDivisionError):
            summary[output_key] = None

    return summary