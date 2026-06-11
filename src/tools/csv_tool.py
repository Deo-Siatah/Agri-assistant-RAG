from src.loaders.csv_loader import load_csv


class CSVTool:

    def __init__(self, file_path):

        self.df = load_csv(file_path)

    # ----------------------------------
    # Dataset Information
    # ----------------------------------

    def describe_dataset(self):

        return {
            "rows": len(self.df),
            "columns": self.df.columns.tolist()
        }

    # ----------------------------------
    # Yield Analytics
    # ----------------------------------

    def average_yield(self):

        avg = self.df[
            "yield_kg"
        ].mean()

        return {
            "metric": "average_yield",
            "value": float(avg)
        }

    def total_yield(self):

        total = self.df["yield_kg"].sum()

        return (
            f"Total yield across all records "
            f"is {total:.2f} kg."
        )

    def highest_yield_county(self):

        county_totals = (
            self.df
            .groupby("county")["yield_kg"]
            .sum()
        )

        county = county_totals.idxmax()

        value = county_totals.max()

        return {
            "metric": "highest_yield_county",
            "county": county,
            "yield_kg": float(value)
        }

    def lowest_yield_county(self):

        county_totals = (
            self.df
            .groupby("county")["yield_kg"]
            .sum()
        )

        county = county_totals.idxmin()

        value = county_totals.min()

        return {
            "metric": "lowest_yield_county",
            "county": county,
            "yield_kg": float(value)
        }

    def top_counties(self, limit=5):

        rankings = (
            self.df
            .groupby("county")["yield_kg"]
            .sum()
            .sort_values(
                ascending=False
            )
            .head(limit)
        )

        result = "Top producing counties:\n"

        for county, value in rankings.items():

            result += (
                f"- {county}: "
                f"{value:.2f} kg\n"
            )

        return result

    # ----------------------------------
    # County Analytics
    # ----------------------------------

    def county_average_yield(self, county):

        county_data = self.df[
            self.df["county"]
            .str.lower()
            == county.lower()
        ]

        if county_data.empty:

            return (
                f"No data found for "
                f"{county}"
            )

        avg = county_data[
            "yield_kg"
        ].mean()

        return (
            f"Average yield in "
            f"{county.title()} "
            f"is {avg:.2f} kg."
        )

    # ----------------------------------
    # Crop Analytics
    # ----------------------------------

    def best_crop(self):

        crops = (
            self.df
            .groupby("crop")["yield_kg"]
            .mean()
        )

        crop = crops.idxmax()

        value = crops.max()

        return (
            f"{crop} has the highest "
            f"average yield at "
            f"{value:.2f} kg."
        )

    # ----------------------------------
    # Rainfall Analytics
    # ----------------------------------

    def rainfall_correlation(self):

        correlation = (
            self.df["rainfall_mm"]
            .corr(
                self.df["yield_kg"]
            )
        )

        return (
            f"Rainfall and yield have "
            f"a correlation of "
            f"{correlation:.2f}."
        )

    def average_rainfall(self):

        avg = (
            self.df["rainfall_mm"]
            .mean()
        )

        return (
            f"Average rainfall is "
            f"{avg:.2f} mm."
        )

    # ----------------------------------
    # Routing
    # ----------------------------------

    def run(self, query):

        query = query.lower()

        if "average yield" in query:
            return self.average_yield()

        if "total yield" in query:
            return self.total_yield()

        if "highest yield" in query:
            return self.highest_yield_county()

        if "lowest yield" in query:
            return self.lowest_yield_county()

        if "top counties" in query:
            return self.top_counties()

        if "best crop" in query:
            return self.best_crop()

        if "rainfall relationship" in query:
            return self.rainfall_correlation()

        if "average rainfall" in query:
            return self.average_rainfall()

        return (
            "I cannot answer that "
            "from the CSV dataset."
        )