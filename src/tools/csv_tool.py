"""
CSV analytics tool — function-based, matching the pattern used elsewhere
(weather_tool, soil_tool). Entry point expected by src/agents/llm_router.py
is query_csv(question).
"""

from __future__ import annotations

from functools import lru_cache

from src.config.settings import get_settings
from src.loaders.csv_loader import load_csv


@lru_cache
def _get_dataframe():
    settings = get_settings()
    return load_csv(settings.csv_path)


# ----------------------------------
# Dataset Information
# ----------------------------------

def describe_dataset():
    df = _get_dataframe()
    return {"rows": len(df), "columns": df.columns.tolist()}


# ----------------------------------
# Yield Analytics
# ----------------------------------

def average_yield():
    df = _get_dataframe()
    avg = df["yield_kg"].mean()
    return {"metric": "average_yield", "value": float(avg)}


def total_yield():
    df = _get_dataframe()
    total = df["yield_kg"].sum()
    return f"Total yield across all records is {total:.2f} kg."


def highest_yield_county():
    df = _get_dataframe()
    county_totals = df.groupby("county")["yield_kg"].sum()
    county = county_totals.idxmax()
    value = county_totals.max()
    return {"metric": "highest_yield_county", "county": county, "yield_kg": float(value)}


def lowest_yield_county():
    df = _get_dataframe()
    county_totals = df.groupby("county")["yield_kg"].sum()
    county = county_totals.idxmin()
    value = county_totals.min()
    return {"metric": "lowest_yield_county", "county": county, "yield_kg": float(value)}


def top_counties(limit=5):
    df = _get_dataframe()
    rankings = (
        df.groupby("county")["yield_kg"].sum().sort_values(ascending=False).head(limit)
    )
    result = "Top producing counties:\n"
    for county, value in rankings.items():
        result += f"- {county}: {value:.2f} kg\n"
    return result


# ----------------------------------
# County Analytics
# ----------------------------------

def county_average_yield(county):
    df = _get_dataframe()
    county_data = df[df["county"].str.lower() == county.lower()]

    if county_data.empty:
        return f"No data found for {county}"

    avg = county_data["yield_kg"].mean()
    return f"Average yield in {county.title()} is {avg:.2f} kg."


# ----------------------------------
# Crop Analytics
# ----------------------------------

def best_crop():
    df = _get_dataframe()
    crops = df.groupby("crop")["yield_kg"].mean()
    crop = crops.idxmax()
    value = crops.max()
    return f"{crop} has the highest average yield at {value:.2f} kg."


# ----------------------------------
# Rainfall Analytics
# ----------------------------------

def rainfall_correlation():
    df = _get_dataframe()
    correlation = df["rainfall_mm"].corr(df["yield_kg"])
    return f"Rainfall and yield have a correlation of {correlation:.2f}."


def average_rainfall():
    df = _get_dataframe()
    avg = df["rainfall_mm"].mean()
    return f"Average rainfall is {avg:.2f} mm."


# ----------------------------------
# Routing
# ----------------------------------

def run(query: str):
    query = query.lower()

    if "average yield" in query:
        return average_yield()
    if "total yield" in query:
        return total_yield()
    if "highest yield" in query:
        return highest_yield_county()
    if "lowest yield" in query:
        return lowest_yield_county()
    if "top counties" in query:
        return top_counties()
    if "best crop" in query:
        return best_crop()
    if "rainfall relationship" in query:
        return rainfall_correlation()
    if "average rainfall" in query:
        return average_rainfall()

    return "I cannot answer that from the CSV dataset."


def query_csv(question: str):
    """Entry point expected by src/agents/llm_router.py."""
    return run(question)