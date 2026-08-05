def route_query(question):

    question = question.lower()

    csv_keywords = [

        "yield",
        "average",
        "total",
        "county",
        "counties",
        "production",
        "dataset",

        "highest",
        "lowest",
        "top",

        "crop",
        "rainfall",
        "correlation",

        "statistics"
    ]

    weather_keywords = [
        "weather",
        "rainfall",
        "temperature",
        "humidity",
        "precipitation",
        "wind",
        "forecast",
        "rain"
    ]

    for keyword in csv_keywords:

        if keyword in question:

            return "csv"
    
    for keyword in weather_keywords:

        if keyword in question:

            return "weather"

    return "pdf"