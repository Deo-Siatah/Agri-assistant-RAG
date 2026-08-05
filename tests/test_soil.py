import pytest
from src.services.soil_service import get_soil_data, SoilServiceError
from src.tools.soil_tool import get_soil_summary

def test_get_soil_data_fetches_real_response():
    # Use coordinates in Kenya (Machakos County area)
    lat, lon = -1.45, 37.25

    try:
        data = get_soil_data(lat, lon)
    except SoilServiceError:
        pytest.fail("SoilGrids API fetch failed")

    # Basic sanity checks
    assert "properties" in data
    assert "layers" in data["properties"]
    assert any(layer["name"] == "phh2o" for layer in data["properties"]["layers"])

def test_get_soil_summary_with_real_data():
    lat, lon = -1.45, 37.25
    summary = get_soil_summary(lat, lon)

    # The summary should contain all expected keys
    assert set(summary.keys()) == {
        "ph", "nitrogen", "organic_carbon", "clay_pct", "sand_pct", "silt_pct"
    }

    # At least one value should not be None
    assert any(value is not None for value in summary.values())
