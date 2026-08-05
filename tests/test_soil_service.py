from unittest.mock import patch

from src.services.soil_service import SoilServiceError
from src.tools.soil_tool import get_soil_summary


SOILGRIDS_EXAMPLE_RESPONSE = {
    "type": "Feature",
    "geometry": {
        "type": "Point",
        "coordinates": [35.2698, 0.5143],
    },
    "properties": {
        "layers": [
            {
                "name": "clay",
                "unit_measure": {
                    "d_factor": 10,
                    "mapped_units": "g/kg",
                    "target_units": "%",
                    "uncertainty_unit": "",
                },
                "depths": [
                    {
                        "range": {
                            "top_depth": 0,
                            "bottom_depth": 5,
                            "unit_depth": "cm",
                        },
                        "label": "0-5cm",
                        "values": {"mean": 425},
                    }
                ],
            },
            {
                "name": "nitrogen",
                "unit_measure": {
                    "d_factor": 100,
                    "mapped_units": "cg/kg",
                    "target_units": "g/kg",
                    "uncertainty_unit": "",
                },
                "depths": [
                    {
                        "range": {
                            "top_depth": 0,
                            "bottom_depth": 5,
                            "unit_depth": "cm",
                        },
                        "label": "0-5cm",
                        "values": {"mean": 259},
                    }
                ],
            },
            {
                "name": "phh2o",
                "unit_measure": {
                    "d_factor": 10,
                    "mapped_units": "pH*10",
                    "target_units": "-",
                    "uncertainty_unit": "",
                },
                "depths": [
                    {
                        "range": {
                            "top_depth": 0,
                            "bottom_depth": 5,
                            "unit_depth": "cm",
                        },
                        "label": "0-5cm",
                        "values": {"mean": 61},
                    }
                ],
            },
            {
                "name": "sand",
                "unit_measure": {
                    "d_factor": 10,
                    "mapped_units": "g/kg",
                    "target_units": "%",
                    "uncertainty_unit": "",
                },
                "depths": [
                    {
                        "range": {
                            "top_depth": 0,
                            "bottom_depth": 5,
                            "unit_depth": "cm",
                        },
                        "label": "0-5cm",
                        "values": {"mean": 320},
                    }
                ],
            },
            {
                "name": "silt",
                "unit_measure": {
                    "d_factor": 10,
                    "mapped_units": "g/kg",
                    "target_units": "%",
                    "uncertainty_unit": "",
                },
                "depths": [
                    {
                        "range": {
                            "top_depth": 0,
                            "bottom_depth": 5,
                            "unit_depth": "cm",
                        },
                        "label": "0-5cm",
                        "values": {"mean": 254},
                    }
                ],
            },
            {
                "name": "soc",
                "unit_measure": {
                    "d_factor": 10,
                    "mapped_units": "dg/kg",
                    "target_units": "g/kg",
                    "uncertainty_unit": "",
                },
                "depths": [
                    {
                        "range": {
                            "top_depth": 0,
                            "bottom_depth": 5,
                            "unit_depth": "cm",
                        },
                        "label": "0-5cm",
                        "values": {"mean": 289},
                    }
                ],
            },
        ]
    },
    "query_time_s": 3.73,
}


def test_get_soil_summary_maps_example_response():

    with patch(
        "src.tools.soil_tool.get_soil_data",
        return_value=SOILGRIDS_EXAMPLE_RESPONSE,
    ):
        result = get_soil_summary(0.5143, 35.2698)

    assert result == {
        "ph": 6.1,
        "nitrogen": 2.59,
        "organic_carbon": 28.9,
        "clay_pct": 42.5,
        "sand_pct": 32.0,
        "silt_pct": 25.4,
    }


def test_get_soil_summary_returns_none_values_on_service_error():

    with patch(
        "src.tools.soil_tool.get_soil_data",
        side_effect=SoilServiceError("boom"),
    ):
        result = get_soil_summary(0.5143, 35.2698)

    assert result == {
        "ph": None,
        "nitrogen": None,
        "organic_carbon": None,
        "clay_pct": None,
        "sand_pct": None,
        "silt_pct": None,
    }
