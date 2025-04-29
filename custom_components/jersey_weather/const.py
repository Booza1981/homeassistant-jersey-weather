"""Constants for the Jersey Weather integration."""

DOMAIN = "jersey_weather"

# API endpoints
FORECAST_URL = "https://prodgojweatherstorage.blob.core.windows.net/data/jerseyForecast.json"
TIDE_URL = "https://prodgojweatherstorage.blob.core.windows.net/data/JerseyTide5Day.json"
COASTAL_REPORTS_URL = "https://prodgojweatherstorage.blob.core.windows.net/data/CoastalReports.json"
SHIPPING_FORECAST_URL = "https://prodgojweatherstorage.blob.core.windows.net/data/Shipping.json"
RADAR_IMAGE_URL = "https://sojpublicdata.blob.core.windows.net/jerseymet/Radar10.JPG"
SATELLITE_IMAGE_URL = "https://sojpublicdata.blob.core.windows.net/jerseymet/Satellite10.JPG"
WIND_WAVES_IMAGE_URL = "https://sojpublicdata.blob.core.windows.net/jerseymet/Wind%20Waves%202018%2049.png"
SEA_STATE_AM_IMAGE_URL = "https://sojpublicdata.blob.core.windows.net/jerseymet/Sea%20State/Sea%20State%20AM.png"
SEA_STATE_PM_IMAGE_URL = "https://sojpublicdata.blob.core.windows.net/jerseymet/Sea%20State/Sea%20State%20PM.png"

# Entity attributes
ATTR_ISSUE_TIME = "issue_time"
ATTR_FORECAST_DATE = "forecast_date"
ATTR_WIND_DIRECTION = "wind_direction"
ATTR_WIND_SPEED = "wind_speed"
ATTR_WIND_SPEED_MPH = "wind_speed_mph"
ATTR_WIND_SPEED_KM = "wind_speed_km"
ATTR_WIND_SPEED_KNOTS = "wind_speed_knots"
ATTR_RAIN_PROBABILITY = "rain_probability"
ATTR_UV_INDEX = "uv_index"
ATTR_PRESSURE = "pressure"
ATTR_PRESSURE_TENDENCY = "pressure_tendency"
ATTR_SEA_TEMPERATURE = "sea_temperature"

# Weather condition mappings from Jersey Weather icons to Home Assistant conditions
CONDITION_MAPPINGS = {
    "a.svg": "sunny",
    "b.svg": "partlycloudy",
    "c.svg": "clear-night",
    "d.svg": "partlycloudy",
    "e.svg": "cloudy",
    "f.svg": "cloudy",
    "g.svg": "fog",
    "h.svg": "rainy",
    "i.svg": "pouring",
    "j.svg": "lightning-rainy",
    "k.svg": "snowy",
    "l.svg": "snowy-rainy",
}

# Tooltip to condition mappings as fallbacks - mapping from tooltip text to HA condition
TOOLTIP_CONDITION_MAPPINGS = {
    "Clear": "clear-night",
    "Fine": "clear-night",
    "Sunny": "sunny",
    "Sunny periods": "partlycloudy",
    "Mainly sunny": "partlycloudy",
    "Sunshine and showers": "rainy",
    "Cloudy": "cloudy",
    "Fair": "clear-night",
    "Fog": "fog",
    "Mist": "fog",
    "Hazy sunshine": "partlycloudy",
    "Sunny intervals": "partlycloudy",
    "Bright": "partlycloudy",
    "Light rain": "rainy",
    "Showers": "rainy",
    "Heavy rain": "pouring",
    "Drizzle": "rainy",
    "Rain": "rainy",
    "Snow": "snowy",
    "Sleet": "snowy-rainy",
    "Thunderstorm": "lightning-rainy",
    "Thunder": "lightning",
}

# Summary condition mappings for inferring conditions from summary text
SUMMARY_CONDITION_MAPPINGS = {
    "sunny": "sunny",
    "clear": "clear-night",
    "fine": "clear-night",
    "cloud": "cloudy",
    "fog": "fog",
    "mist": "fog",
    "rain": "rainy",
    "shower": "rainy",
    "thunder": "lightning-rainy",
    "snow": "snowy",
    "sleet": "snowy-rainy",
    "hail": "hail",
    "lightning": "lightning",
    "storm": "lightning-rainy",
    "drizzle": "rainy",
    "overcast": "cloudy",
}